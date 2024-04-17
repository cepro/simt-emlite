from decimal import Decimal
from typing import TypedDict, List
from kaitaistruct import KaitaiStream, BytesIO
from emlite_mediator.emlite.messages.emlite_data import EmliteData
from emlite_mediator.mediator.grpc.exception.EmliteConnectionFailure import (
    EmliteConnectionFailure,
)
from emlite_mediator.mediator.grpc.exception.EmliteEOFError import EmliteEOFError
from emlite_mediator.util.logging import get_logger

import datetime
import grpc
import os

from emlite_mediator.emlite.messages.emlite_object_id_enum import ObjectIdEnum

from .grpc.client import EmliteMediatorGrpcClient

logger = get_logger(__name__, __file__)


class MediatorClientException(Exception):
    def __init__(self, code_str, message):
        self.code_str = code_str
        self.message = message
        super().__init__(self.message)


# 8 blocks x 8 rates for tariff pricings
PricingTable = List[List[Decimal]]


def emop_price_amount_to_decimal(amount: Decimal) -> Decimal:
    return amount / Decimal(100000)


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


class EmliteMediatorClient:
    def __init__(self, host="0.0.0.0", port=51498, meter_id=None):
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

        # assemble the request payload manually
        data_rec_length = 5 + len(token_bytes)
        data_rec = EmliteData(data_rec_length)

        data_rec.format = b"\x01"
        data_rec.object_id = ObjectIdEnum.prepay_token_send.value.to_bytes(
            3, byteorder="big"
        )
        data_rec.read_write = EmliteData.ReadWriteFlags.write
        data_rec.payload = token_bytes

        kt_stream = KaitaiStream(BytesIO(bytearray(data_rec_length)))
        data_rec._write(kt_stream)
        message_bytes = kt_stream.to_byte_array()

        self._send_message(message_bytes)

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
            "standing_charge": emop_price_amount_to_decimal(standing_charge_rec.value),
            "price_current": emop_price_amount_to_decimal(price_rec.value),
            "price_index_current": price_index_rec.value,
            "tou_rate_current": tou_rate_rec.value,
            "block_rate_current": block_rate_rec.value,
            "prepayment_debt_recovery_rate": emop_price_amount_to_decimal(
                debt_recovery_rec.value
            ),
            "prepayment_ecredit_availability": emop_price_amount_to_decimal(
                ecredit_rec.value
            ),
            "prepayment_emergency_credit": emop_price_amount_to_decimal(
                emergency_credit_rec.value
            ),
            "pricings": pricings,
        }

    def tariffs_future_read(self) -> TariffsFuture:
        standing_charge_rec = self._read_element(
            ObjectIdEnum.tariff_active_standing_charge
        )
        self.log.debug("standing charge", value=standing_charge_rec.value)

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
            "standing_charge": emop_price_amount_to_decimal(standing_charge_rec.value),
            "prepayment_debt_recovery_rate": emop_price_amount_to_decimal(
                debt_recovery_rec.value
            ),
            "prepayment_ecredit_availability": emop_price_amount_to_decimal(
                ecredit_rec.value
            ),
            "prepayment_emergency_credit": emop_price_amount_to_decimal(
                emergency_credit_rec.value
            ),
            "pricings": pricings,
        }

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
        # assemble the request payload manually
        payload = bytes(80)  # all switches off - all zeros
        data_rec_length = 5 + len(payload)
        data_rec = EmliteData(data_rec_length)

        data_rec.format = b"\x01"
        data_rec.object_id = object_id.value.to_bytes(3, byteorder="big")
        data_rec.read_write = EmliteData.ReadWriteFlags.write
        data_rec.payload = payload

        kt_stream = KaitaiStream(BytesIO(bytearray(data_rec_length)))
        data_rec._write(kt_stream)
        message_bytes = kt_stream.to_byte_array()

        self._send_message(message_bytes)

    def _tariffs_pricing_blocks_read(self, is_active: bool) -> PricingTable:
        # create a pricings table with all values initialised to Decimal zero
        pricings: PricingTable = [[Decimal("0") for _ in range(8)] for _ in range(8)]

        for block in range(1, 9):
            for rate in range(1, 9):
                object_id_str = f"tariff_{'active' if is_active else 'future'}_block_{block}_rate_{rate}"

                print(object_id_str)

                price_rec = self._read_element(ObjectIdEnum[object_id_str])
                self.log.debug(price_rec.value)

                pricings[block - 1][rate - 1] = emop_price_amount_to_decimal(
                    price_rec.value
                )

        return pricings

    def _read_element(self, object_id):
        try:
            data = self.grpc_client.read_element(object_id)
        except EmliteConnectionFailure as e:
            raise MediatorClientException("EMLITE_CONNECTION_FAILURE", e.message)
        except EmliteEOFError as e:
            raise MediatorClientException("EMLITE_EOF_ERROR", e.message)
        except grpc.RpcError as e:
            raise MediatorClientException(e.code().name, e.details())
        return data

    def _send_message(self, message: bytes):
        try:
            data = self.grpc_client.send_message(message)
        except grpc.RpcError as e:
            raise MediatorClientException(e.code().name, e.details())
        return data


if __name__ == "__main__":
    mediator_port: str = os.environ.get("MEDIATOR_PORT")

    client = EmliteMediatorClient(port=mediator_port)
    # print(client.three_phase_instantaneous_voltage())
    # print(client.csq())

    # print(client.prepay_send_token('53251447227692530360'))
    # print(client.prepay_enabled())

    print(client.tariffs_active_read())
    # print(client.tariffs_future_read())

    # client.tariffs_time_switches_element_a_or_single_write()
    # client.tariffs_time_switches_element_b_write()
    # print(client.tariffs_time_switches_element_a_or_single_read())
    # print(client.tariffs_time_switches_element_b_read())
