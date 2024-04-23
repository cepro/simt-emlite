import datetime
import sys
from decimal import Decimal
from typing import List, TypedDict

import fire
import grpc

from emlite_mediator.emlite.emlite_util import (
    emop_encode_amount_as_u4le_rec,
    emop_encode_timestamp_as_u4le_rec,
    emop_epoch_seconds_to_datetime,
    emop_format_firmware_version,
    emop_scale_price_amount,
)
from emlite_mediator.emlite.messages.emlite_object_id_enum import ObjectIdEnum
from emlite_mediator.mediator.grpc.exception.EmliteConnectionFailure import (
    EmliteConnectionFailure,
)
from emlite_mediator.mediator.grpc.exception.EmliteEOFError import EmliteEOFError
from emlite_mediator.util.logging import get_logger

from .grpc.client import EmliteMediatorGrpcClient

logger = get_logger(__name__, __file__)


class MediatorClientException(Exception):
    def __init__(self, code_str, message):
        self.code_str = code_str
        self.message = message
        super().__init__(self.message)


# 8 blocks x 8 rates for tariff pricings
PricingTable = List[List[Decimal]]


class TariffsActive(TypedDict):
    standing_charge: Decimal

    threshold_mask: List[bool]
    threshold_values: List[int]

    price_current: Decimal
    price_index_current: int
    tou_rate_current: int
    block_rate_current: int

    prepayment_emergency_credit: Decimal
    prepayment_ecredit_availability: Decimal
    prepayment_debt_recovery_rate: Decimal

    gas: Decimal

    element_b_tou_rate_current: int
    element_b_block_rate_current: int
    element_b_price_index_current: int

    element_b_tou_rate_1: Decimal
    element_b_tou_rate_2: Decimal
    element_b_tou_rate_3: Decimal
    element_b_tou_rate_4: Decimal

    pricings: PricingTable


class TariffsFuture(TypedDict):
    tou_flag: bool

    standing_charge: Decimal

    threshold_mask: List[bool]
    threshold_values: List[int]

    activation_datetime: datetime

    gas: Decimal

    prepayment_emergency_credit: Decimal
    prepayment_ecredit_availability: Decimal
    prepayment_debt_recovery_rate: Decimal

    element_b_tou_rate_1: Decimal
    element_b_tou_rate_2: Decimal
    element_b_tou_rate_3: Decimal
    element_b_tou_rate_4: Decimal

    pricings: PricingTable


"""
    Use this class to make calls to an emlite meter through a mediator server.

    This is a wrapper around the gRPC client interface to the mediator server
    providing convencience functions to request each peice of data and get
    back a meaningful typed response.
"""


class EmliteMediatorClient(object):
    def __init__(self, port, meter_id=None, host="0.0.0.0"):
        self.grpc_client = EmliteMediatorGrpcClient(host, port, meter_id)
        global logger
        self.log = logger.bind(meter_id=meter_id, mediator_port=port)
        self.log.info("port", port=port)
        # self.log.debug('EmliteMediatorClient init')

    def serial(self) -> str:
        data = self._read_element(ObjectIdEnum.serial)
        serial = data.serial.strip()
        self.log.info("received serial", serial=serial)
        return serial

    def hardware(self) -> str:
        data = self._read_element(ObjectIdEnum.hardware_version)
        hardware = data.hardware.replace("\u0000", "").strip()
        self.log.info("received hardware", hardware=hardware)
        return hardware

    def firmware_version(self) -> str:
        data = self._read_element(ObjectIdEnum.firmware_version)
        version_bytes = bytearray(data.version_bytes)
        if len(version_bytes) == 4:
            # single phase meter
            version_str = emop_format_firmware_version(version_bytes.decode("ASCII"))
        else:
            # three phase meter
            version_str = version_bytes.hex()
        self.log.info("firmware version", firmware_version=version_str)
        return version_str

    def clock_time(self) -> datetime:
        data = self._read_element(ObjectIdEnum.time)
        date_obj = datetime.datetime(
            2000 + data.year, data.month, data.date, data.hour, data.minute, data.second
        )
        self.log.info("received time", time=date_obj.isoformat())
        return date_obj

    def csq(self) -> int:
        data = self._read_element(ObjectIdEnum.csq_net_op)
        self.log.info("received csq", csq=data.csq)
        return data.csq

    def instantaneous_voltage(self) -> float:
        data = self._read_element(ObjectIdEnum.instantaneous_voltage)
        self.log.info("received instantaneous voltage", voltage=data.voltage)
        return data.voltage

    def prepay_enabled(self) -> bool:
        data = self._read_element(ObjectIdEnum.prepay_enabled_flag)
        enabled: bool = data.enabled_flag == 1
        self.log.info("received prepay enabled flag", prepay_enabled_flag=enabled)
        return enabled

    def prepay_balance(self) -> float:
        data = self._read_element(ObjectIdEnum.prepay_balance)
        self.log.debug("received prepay balance", prepay_balance_raw=data.balance)
        balance_gbp: float = data.balance / 100000
        self.log.info("prepay balance in GBP", prepay_balance_gbp=balance_gbp)
        return balance_gbp

    def prepay_send_token(self, token: str):
        token_bytes = token.encode("ascii")
        self._write_element(ObjectIdEnum.prepay_token_send, token_bytes)

    def prepay_transaction_count(self) -> int:
        data = self._read_element(ObjectIdEnum.monetary_info_transaction_count)
        self.log.debug(
            "received prepay transaction count", transaction_count=data.count
        )
        return data.count

    def three_phase_instantaneous_voltage(self) -> tuple[float, float, float]:
        vl1 = self._read_element(ObjectIdEnum.three_phase_instantaneous_voltage_l1)

        # wrapping second in a try as that's where we are seeing these
        # EOFErrors - for now want to make them warnings rather than fail
        #   but they do need fixing eventually
        try:
            vl2 = self._read_element(ObjectIdEnum.three_phase_instantaneous_voltage_l2)
        except EmliteEOFError as e:
            self.log.warn("3p v2 failed - setting to None (e=" + e + ")")
            vl2 = None

        # wrapping the third as well as now that second errors are handled
        # errors may occur on the third
        try:
            vl3 = self._read_element(ObjectIdEnum.three_phase_instantaneous_voltage_l3)
        except EmliteEOFError as e:
            self.log.warn("3p v3 failed - setting to None (e=" + e + ")")
            vl3 = None

        return (
            vl1.voltage / 10,
            None if vl2 is None else vl2.voltage / 10,
            None if vl3 is None else vl3.voltage / 10,
        )

    def tariffs_active_read(self) -> TariffsActive:
        standing_charge_rec = self._read_element(
            ObjectIdEnum.tariff_active_standing_charge
        )
        self.log.debug("standing charge", value=standing_charge_rec.value)

        price_rec = self._read_element(ObjectIdEnum.tariff_active_price)
        self.log.debug("price", value=price_rec.value)

        price_index_rec = self._read_element(
            ObjectIdEnum.tariff_active_price_index_current
        )
        self.log.debug("price index", value=price_index_rec.value)

        tou_rate_rec = self._read_element(ObjectIdEnum.tariff_active_tou_rate_current)
        self.log.debug("tou rate", value=tou_rate_rec.value)

        block_rate_rec = self._read_element(
            ObjectIdEnum.tariff_active_block_rate_current
        )
        self.log.debug("block rate", value=block_rate_rec.value)

        emergency_credit_rec = self._read_element(
            ObjectIdEnum.tariff_active_prepayment_emergency_credit
        )
        self.log.debug("emergency credit", value=emergency_credit_rec.value)

        ecredit_rec = self._read_element(
            ObjectIdEnum.tariff_active_prepayment_ecredit_availability
        )
        self.log.debug("ecredit", value=ecredit_rec.value)

        debt_recovery_rec = self._read_element(
            ObjectIdEnum.tariff_active_prepayment_debt_recovery_rate
        )
        self.log.debug("debt recovery rate", value=debt_recovery_rec.value)

        pricings = self._tariffs_pricing_blocks_read(True)
        self.log.debug("pricings", pricings=pricings)

        return {
            "standing_charge": emop_scale_price_amount(standing_charge_rec.value),
            "price_current": emop_scale_price_amount(price_rec.value),
            "price_index_current": price_index_rec.value,
            "tou_rate_current": tou_rate_rec.value,
            "block_rate_current": block_rate_rec.value,
            "prepayment_debt_recovery_rate": emop_scale_price_amount(
                debt_recovery_rec.value
            ),
            "prepayment_ecredit_availability": emop_scale_price_amount(
                ecredit_rec.value
            ),
            "prepayment_emergency_credit": emop_scale_price_amount(
                emergency_credit_rec.value
            ),
            "pricings": pricings,
        }

    def tariffs_future_read(self) -> TariffsFuture:
        standing_charge_rec = self._read_element(
            ObjectIdEnum.tariff_future_standing_charge
        )
        self.log.debug("standing charge", value=standing_charge_rec.value)

        activation_timestamp_rec = self._read_element(
            ObjectIdEnum.tariff_future_activation_datetime
        )
        self.log.debug("activation timestamp", value=activation_timestamp_rec.value)

        emergency_credit_rec = self._read_element(
            ObjectIdEnum.tariff_future_prepayment_emergency_credit
        )
        self.log.debug("emergency credit", value=emergency_credit_rec.value)

        ecredit_rec = self._read_element(
            ObjectIdEnum.tariff_future_prepayment_ecredit_availability
        )
        self.log.debug("ecredit", value=ecredit_rec.value)

        debt_recovery_rec = self._read_element(
            ObjectIdEnum.tariff_future_prepayment_debt_recovery_rate
        )
        self.log.debug("debt recovery rate", value=debt_recovery_rec.value)

        pricings = self._tariffs_pricing_blocks_read(False)
        self.log.debug("pricings", pricings=pricings)

        return {
            "standing_charge": emop_scale_price_amount(standing_charge_rec.value),
            "activation_datetime": emop_epoch_seconds_to_datetime(
                activation_timestamp_rec.value
            ),
            "prepayment_debt_recovery_rate": emop_scale_price_amount(
                debt_recovery_rec.value
            ),
            "prepayment_ecredit_availability": emop_scale_price_amount(
                ecredit_rec.value
            ),
            "prepayment_emergency_credit": emop_scale_price_amount(
                emergency_credit_rec.value
            ),
            "pricings": pricings,
        }

    def tariffs_future_write(
        self, from_ts: datetime, standing_charge: Decimal, unit_rate: Decimal
    ):
        unit_rate_encoded = emop_encode_amount_as_u4le_rec(unit_rate)

        # block threshold mask and values - set all to zeros to switch off
        self.log.debug("zero out threshold mask")
        self._write_element(
            ObjectIdEnum.tariff_future_threshold_mask,
            bytes(1),
        )

        self.log.debug("zero out all threshold values")
        self._write_element(ObjectIdEnum.tariff_future_threshold_values, bytes(14))

        # TOU and rates
        # - turn flag off
        # - set each B element rate to the single fixed rate
        # - TODO: check behavior - will it charge at TOU Rate 1 always?
        self.log.debug("switch off tou flag")
        self._write_element(ObjectIdEnum.tariff_future_tou_flag, bytes(1))

        self.log.debug(f"set element b tou rates to {unit_rate}")
        self._write_element(
            ObjectIdEnum.tariff_future_element_b_tou_rate_1, unit_rate_encoded
        )
        self._write_element(
            ObjectIdEnum.tariff_future_element_b_tou_rate_2, unit_rate_encoded
        )
        self._write_element(
            ObjectIdEnum.tariff_future_element_b_tou_rate_3, unit_rate_encoded
        )
        self._write_element(
            ObjectIdEnum.tariff_future_element_b_tou_rate_4, unit_rate_encoded
        )

        # prepayment amounts
        # TODO: decide what these should be - setting dummy values for now
        self.log.debug("set prepayment amounts")
        self._write_element(
            ObjectIdEnum.tariff_future_prepayment_emergency_credit,
            emop_encode_amount_as_u4le_rec(Decimal("8.88")),
        )
        self._write_element(
            ObjectIdEnum.tariff_future_prepayment_ecredit_availability,
            emop_encode_amount_as_u4le_rec(Decimal("7.77")),
        )
        self._write_element(
            ObjectIdEnum.tariff_future_prepayment_debt_recovery_rate,
            emop_encode_amount_as_u4le_rec(Decimal("6.66")),
        )

        # gas tariff - set to zero as it doesn't apply
        self.log.debug("set gas rate to zero")
        self._write_element(ObjectIdEnum.tariff_future_gas, bytes(4))

        # block 1 / rate 1 - set to the single rate
        self.log.debug(f"set block 1 rate 1 to {unit_rate}")
        self._write_element(
            ObjectIdEnum.tariff_future_block_1_rate_1, unit_rate_encoded
        )

        # set all the other block / units to zero
        #
        # TODO: likely this is unncessary as only block 1 / rate 1 is required
        # however that hasn't been confirmed for sure yet. so for now let's
        # make the table a clean slate of zero values
        zero_rate_bytes = bytes(4)
        for block in range(1, 9):
            for rate in range(1, 9):
                if block == 1 and rate == 1:
                    continue
                object_id_str = f"tariff_future_block_{block}_rate_{rate}"
                self._write_element(ObjectIdEnum[object_id_str], zero_rate_bytes)
                self.log.debug(f"{object_id_str} set to zero")

        # standing charge (daily charge)
        self.log.debug(f"set standing charge to {standing_charge}")
        self._write_element(
            ObjectIdEnum.tariff_future_standing_charge,
            emop_encode_amount_as_u4le_rec(standing_charge),
        )

        # datetime to activate these tariffs
        self.log.debug(f"set activation date to {from_ts}")
        self._write_element(
            ObjectIdEnum.tariff_future_activation_datetime,
            emop_encode_timestamp_as_u4le_rec(from_ts),
        )

    def tariffs_future_write_str_args(
        self, from_ts_iso_str: str, standing_charge_str: str, unit_rate_str: str
    ):
        self._check_amount_arg_is_string(standing_charge_str)
        self._check_amount_arg_is_string(unit_rate_str)
        self.tariffs_future_write(
            datetime.datetime.fromisoformat(from_ts_iso_str),
            standing_charge=Decimal(standing_charge_str),
            unit_rate=Decimal(unit_rate_str),
        )

    def tariffs_time_switches_element_a_or_single_read(self) -> bytes:
        data = self._read_element(ObjectIdEnum.tariff_time_switch_element_a_or_single)
        self.log.debug("element A switch settings", value=data.switch_settings)
        return data.switch_settings

    def tariffs_time_switches_element_a_or_single_write(self):
        self._tariffs_time_switches_write(
            ObjectIdEnum.tariff_time_switch_element_a_or_single
        )

    def tariffs_time_switches_element_b_read(self) -> bytes:
        data = self._read_element(ObjectIdEnum.tariff_time_switch_element_b)
        self.log.debug("element B switch settings", value=data.switch_settings)
        return data.switch_settings

    def tariffs_time_switches_element_b_write(self):
        self._tariffs_time_switches_write(ObjectIdEnum.tariff_time_switch_element_b)

    def _tariffs_time_switches_write(self, object_id: ObjectIdEnum):
        payload = bytes(80)  # all switches off - all zeros
        self._write_element(object_id, payload)

    def _tariffs_pricing_blocks_read(self, is_active: bool) -> PricingTable:
        # create a pricings table with all values initialised to Decimal zero
        pricings: PricingTable = [[Decimal("0") for _ in range(8)] for _ in range(8)]

        for block in range(1, 9):
            for rate in range(1, 9):
                object_id_str = f"tariff_{'active' if is_active else 'future'}_block_{block}_rate_{rate}"
                price_rec = self._read_element(ObjectIdEnum[object_id_str])
                self.log.debug(f"{object_id_str}={price_rec.value}")
                pricings[block - 1][rate - 1] = emop_scale_price_amount(price_rec.value)

        return pricings

    def _read_element(self, object_id: ObjectIdEnum):
        try:
            data = self.grpc_client.read_element(object_id)
        except EmliteConnectionFailure as e:
            raise MediatorClientException("EMLITE_CONNECTION_FAILURE", e.message)
        except EmliteEOFError as e:
            raise MediatorClientException("EMLITE_EOF_ERROR", e.message)
        except grpc.RpcError as e:
            raise MediatorClientException(e.code().name, e.details())
        return data

    def _write_element(self, object_id: ObjectIdEnum, payload: bytes):
        try:
            self.grpc_client.write_element(object_id, payload)
        except EmliteConnectionFailure as e:
            raise MediatorClientException("EMLITE_CONNECTION_FAILURE", e.message)
        except EmliteEOFError as e:
            raise MediatorClientException("EMLITE_EOF_ERROR", e.message)
        except grpc.RpcError as e:
            raise MediatorClientException(e.code().name, e.details())

    def _send_message(self, message: bytes):
        try:
            data = self.grpc_client.send_message(message)
        except grpc.RpcError as e:
            raise MediatorClientException(e.code().name, e.details())
        return data

    def _check_amount_arg_is_string(self, arg_value):
        if isinstance(arg_value, str):
            return
        print(
            "\nERROR: amount argument passed as floating point number. pass "
            + "as string to avoid floating point rounding errors "
            + "[eg. \"'0.234'\" or '\"0.234\"']"
        )
        sys.exit(10)


if __name__ == "__main__":
    fire.Fire(EmliteMediatorClient)
