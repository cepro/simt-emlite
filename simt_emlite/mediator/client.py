# mypy: disable-error-code="import-untyped"
import datetime
import logging
from datetime import time
from decimal import Decimal
from typing import Any, Dict, List, TypedDict, cast
from zoneinfo import ZoneInfo

import grpc
from emop_frame_protocol.emop_data import EmopData
from emop_frame_protocol.emop_event_log_response import EmopEventLogResponse
from emop_frame_protocol.emop_message import EmopMessage
from emop_frame_protocol.emop_object_id_enum import ObjectIdEnum
from emop_frame_protocol.emop_profile_log_1_response import (
    EmopProfileLog1Response,
    emop_decode_profile_log_1_response,
)
from emop_frame_protocol.emop_profile_log_2_response import (
    EmopProfileLog2Response,
    emop_decode_profile_log_2_response,
)
from emop_frame_protocol.emop_profile_three_phase_intervals_response_block import (
    EmopProfileThreePhaseIntervalsResponseBlock,
)
from emop_frame_protocol.emop_profile_three_phase_intervals_response_frame import (
    EmopProfileThreePhaseIntervalsResponseFrame,
)
from emop_frame_protocol.generated.emop_event_log_request import (
    EmopEventLogRequest,
)
from emop_frame_protocol.generated.emop_profile_log_request import EmopProfileLogRequest
from emop_frame_protocol.generated.emop_profile_three_phase_intervals_request import (
    EmopProfileThreePhaseIntervalsRequest,
)
from emop_frame_protocol.util import (
    emop_datetime_to_epoch_seconds,
    emop_encode_amount_as_u4le_rec,
    emop_encode_datetime_to_time_rec,
    emop_encode_object_id,
    emop_encode_timestamp_as_u4le_rec,
    emop_epoch_seconds_to_datetime,
    emop_format_firmware_version,
    emop_obis_triplet_to_decimal,
    emop_scale_price_amount,
)
from emop_frame_protocol.vendor.kaitaistruct import BytesIO, KaitaiStream

from simt_emlite.dto.three_phase_intervals import ThreePhaseIntervals
from simt_emlite.mediator.grpc.exception.EmliteConnectionFailure import (
    EmliteConnectionFailure,
)
from simt_emlite.mediator.grpc.exception.EmliteEOFError import EmliteEOFError
from simt_emlite.util.logging import get_logger
from simt_emlite.util.three_phase_intervals import (
    blocks_to_intervals_rec,
    export_three_phase_intervals_to_csv,
)

from .grpc.client import EmliteMediatorGrpcClient
from .mediator_client_exception import MediatorClientException

logger = get_logger(__name__, __file__)


# 8 blocks x 8 rates for tariff pricings
PricingTable = List[List[Decimal]]


class TariffsActive(TypedDict):
    standing_charge: str

    unit_rate_element_a: str
    unit_rate_element_b: str

    threshold_mask: Dict[str, int]
    threshold_values: Dict[str, bool]

    price_current: Decimal | None
    price_index_current: int | None
    tou_rate: int | None
    block_rate: int | None

    prepayment_emergency_credit: str
    prepayment_ecredit_availability: str
    prepayment_debt_recovery_rate: str

    gas: Decimal | None

    element_b_tou_rate: int
    element_b_block_rate: int | None
    element_b_price_index_current: int | None

    element_b_tou_rate_1: Decimal | None
    element_b_tou_rate_2: Decimal | None
    element_b_tou_rate_3: Decimal | None
    element_b_tou_rate_4: Decimal | None

    pricings: PricingTable | None


class TariffsFuture(TypedDict):
    standing_charge: str

    unit_rate_element_a: str
    unit_rate_element_b: str

    threshold_mask: Dict[str, int]
    threshold_values: Dict[str, bool]

    activation_datetime: datetime.datetime

    prepayment_emergency_credit: str
    prepayment_ecredit_availability: str
    prepayment_debt_recovery_rate: str

    element_b_tou_rate_1: Decimal | None
    element_b_tou_rate_2: Decimal | None
    element_b_tou_rate_3: Decimal | None
    element_b_tou_rate_4: Decimal | None

    pricings: PricingTable | None


"""
    Use this class to make calls to an emlite meter through a mediator server.

    This is a wrapper around the gRPC client interface to the mediator server
    providing convencience functions to request each peice of data and get
    back a meaningful typed response.
"""


class EmliteMediatorClient(object):
    def __init__(
        self,
        mediator_address: str = "0.0.0.0:50051",
        meter_id: str | None = None,
        use_cert_auth: bool = False,
        logging_level: str | int = logging.INFO,
    ) -> None:
        self.grpc_client = EmliteMediatorGrpcClient(
            mediator_address=mediator_address,
            meter_id=meter_id,
            use_cert_auth=use_cert_auth,
        )

        logging.getLogger().setLevel(logging_level)
        # logging.getLogger("simt_emlite.mediator.grpc.client").setLevel(logging.WARN)

        global logger
        self.log = logger.bind(mediator_address=mediator_address, meter_id=meter_id)
        self.log.debug("EmliteMediatorClient init")

    def serial_read(self) -> str:
        data = self._read_element(ObjectIdEnum.serial)
        serial: str = data.serial.strip()
        self.log.info("received serial", serial=serial)
        return serial

    def hardware(self) -> str:
        data = self._read_element(ObjectIdEnum.hardware_version)

        # if blank then it's a three phase meter
        if data.hardware == "":
            config = self.three_phase_hardware_configuration()
            if config.meter_type == EmopMessage.ThreePhaseMeterType.ax_whole_current:
                hardware = "P1.ax"
            elif config.meter_type == EmopMessage.ThreePhaseMeterType.cx_ct_operated:
                hardware = "P1.cx"
            else:
                hardware = "THREE_PHASE_UNKNOWN"
        else:
            hardware = data.hardware.replace("\u0000", "").strip()

        self.log.info("hardware", hardware=hardware)
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
        return str(version_str)

    def clock_time_read(self) -> datetime.datetime:
        data = self._read_element(ObjectIdEnum.time)
        date_obj = datetime.datetime(
            2000 + data.year,
            data.month,
            data.date,
            data.hour,
            data.minute,
            data.second,
            tzinfo=datetime.timezone.utc,
        )
        self.log.info("received time", time=date_obj.isoformat())
        return date_obj

    def clock_time_write(self) -> None:
        time_bytes = emop_encode_datetime_to_time_rec(
            datetime.datetime.now(tz=datetime.timezone.utc)
        )
        self._write_element(ObjectIdEnum.time, time_bytes)

    def csq(self) -> int:
        data = self._read_element(ObjectIdEnum.csq_net_op)
        self.log.info("received csq", csq=data.csq)
        return cast(int, data.csq)

    def instantaneous_voltage(self) -> float:
        data = self._read_element(ObjectIdEnum.instantaneous_voltage)
        self.log.info("received instantaneous voltage", voltage=data.voltage)
        return float(data.voltage)

    def instantaneous_active_power(self) -> float:
        data = self._read_element(ObjectIdEnum.instantaneous_active_power)
        power_kwh = data.power / 1000
        self.log.info("received instantaneous active power", power_kwh=power_kwh)
        return float(power_kwh)

    def instantaneous_active_power_element_a(self) -> float:
        data = self._read_element(
            ObjectIdEnum.element_a_instantaneous_active_power_import
        )
        power_kwh = data.power / 1000
        self.log.info(
            "received instantaneous active power (element a)", power_kwh=power_kwh
        )
        return float(power_kwh)

    def instantaneous_active_power_element_b(self) -> float:
        data = self._read_element(
            ObjectIdEnum.element_b_instantaneous_active_power_import
        )
        power_kwh = data.power / 1000
        self.log.info(
            "received instantaneous active power (element b)", power_kwh=power_kwh
        )
        return float(power_kwh)

    def read_element_a(self) -> EmopMessage.ReadingRec:
        data = self._read_element(ObjectIdEnum.read_element_a)
        self.log.info(
            "received read_element_a record",
            import_active=data.import_active,
            export_active=data.export_active,
            import_reactive=data.import_reactive,
            export_reactive=data.export_reactive,
        )
        return data

    def read_element_b(self) -> EmopMessage.ReadingRec:
        data = self._read_element(ObjectIdEnum.read_element_b)
        self.log.info(
            "received read_element_b record",
            import_active=data.import_active,
            export_active=data.export_active,
            import_reactive=data.import_reactive,
            export_reactive=data.export_reactive,
        )
        return data

    def daylight_savings_correction_enabled(self) -> bool:
        data = self._read_element(ObjectIdEnum.daylight_savings_correction_flag)
        enabled: bool = data.enabled_flag == 1
        self.log.info(
            "received daylight savings correction flag",
            daylight_savings_correction_flag=enabled,
        )
        return enabled

    def daylight_savings_correction_enabled_write(self, enabled: bool) -> None:
        flag_bytes = bytes.fromhex("01" if enabled else "00")
        self._write_element(ObjectIdEnum.daylight_savings_correction_flag, flag_bytes)

    def backlight(self) -> EmopMessage.BacklightSettingType:
        data = self._read_element(ObjectIdEnum.backlight)
        self.log.info("received backlight setting", backlight_setting=data.setting)
        return data.setting

    def backlight_write(self, setting: EmopMessage.BacklightSettingType) -> None:
        setting_bytes = bytes([setting.value])
        self._write_element(ObjectIdEnum.backlight, setting_bytes)

    def load_switch(self) -> EmopMessage.LoadSwitchSettingType:
        data = self._read_element(ObjectIdEnum.load_switch)
        self.log.info("received load switch setting", load_switch_setting=data.setting)
        return data.setting

    def load_switch_write(self, setting: EmopMessage.LoadSwitchSettingType) -> None:
        setting_bytes = bytes([setting.value])
        self._write_element(ObjectIdEnum.load_switch, setting_bytes)

    def prepay_enabled(self) -> bool:
        data = self._read_element(ObjectIdEnum.prepay_enabled_flag)
        enabled: bool = data.enabled_flag == 1
        self.log.info("received prepay enabled flag", prepay_enabled_flag=enabled)
        return enabled

    def prepay_no_debt_recovery_when_emergency_credit_enabled(self) -> bool:
        data = self._read_element(
            ObjectIdEnum.prepay_no_debt_recovery_when_emergency_credit_flag
        )
        enabled: bool = data.enabled_flag == 1
        self.log.info(
            "received no debt recovery when in emergency credit flag",
            prepay_no_debt_recovery_when_emergency_credit_flag=enabled,
        )
        return enabled

    def prepay_no_standing_charge_when_power_fail_enabled(self) -> bool:
        data = self._read_element(
            ObjectIdEnum.prepay_no_standing_charge_when_power_fail_flag
        )
        enabled: bool = data.enabled_flag == 1
        self.log.info(
            "received no standing charge when power fail flag",
            prepay_no_standing_charge_when_power_fail_flag=enabled,
        )
        return enabled

    def prepay_enabled_write(self, enabled: bool) -> None:
        if enabled:
            balance_gbp = self.prepay_balance()
            if balance_gbp < 10.0:
                raise Exception(
                    f"balance {balance_gbp} too low to enable prepay mode (< 10.0). add more credit and try again."
                )
        flag_bytes = bytes.fromhex("01" if enabled else "00")
        self._write_element(ObjectIdEnum.prepay_enabled_flag, flag_bytes)

    def prepay_balance(self) -> Decimal:
        data = self._read_element(ObjectIdEnum.prepay_balance)
        self.log.debug("received prepay balance", prepay_balance_raw=data.balance)
        balance_gbp: Decimal = emop_scale_price_amount(Decimal(data.balance))
        self.log.info("prepay balance in GBP", prepay_balance_gbp=balance_gbp)
        return balance_gbp

    def prepay_send_token(self, token: str) -> None:
        token_bytes = token.encode("ascii")
        self._write_element(ObjectIdEnum.prepay_token_send, token_bytes)

    def prepay_transaction_count(self) -> int:
        data = self._read_element(ObjectIdEnum.monetary_info_transaction_count)
        self.log.info("received prepay transaction count", transaction_count=data.count)
        return cast(int, data.count)

    def three_phase_serial(self) -> str:
        data = self._read_element(ObjectIdEnum.three_phase_serial)
        serial = data.serial.strip()
        self.log.info("received three phase serial", serial=serial)
        return cast(str, serial)

    def three_phase_read(
        self,
    ) -> Dict[str, float | None]:
        active_import: EmopMessage.U4leValueRec | None = self._safe_read_element(
            ObjectIdEnum.three_phase_total_active_import
        )
        active_export: EmopMessage.U4leValueRec | None = self._safe_read_element(
            ObjectIdEnum.three_phase_total_active_export
        )
        reactive_import: EmopMessage.U4leValueRec | None = self._safe_read_element(
            ObjectIdEnum.three_phase_total_reactive_import
        )
        reactive_export: EmopMessage.U4leValueRec | None = self._safe_read_element(
            ObjectIdEnum.three_phase_total_reactive_export
        )
        apparent_import: EmopMessage.U4leValueRec | None = self._safe_read_element(
            ObjectIdEnum.three_phase_total_apparent_import
        )
        apparent_export: EmopMessage.U4leValueRec | None = self._safe_read_element(
            ObjectIdEnum.three_phase_total_apparent_export
        )

        reads_dict: Dict[str, float | None] = {
            "active_import": self._scale_kilo_value(active_import),
            "active_export": self._scale_kilo_value(active_export),
            "reactive_import": self._scale_kilo_value(reactive_import),
            "reactive_export": self._scale_kilo_value(reactive_export),
            "apparent_import": self._scale_kilo_value(apparent_import),
            "apparent_export": self._scale_kilo_value(apparent_export),
        }

        self.log.info(f"reads: {reads_dict}")

        return reads_dict

    def three_phase_instantaneous_voltage(
        self,
    ) -> tuple[float, float | None, float | None]:
        vl1 = self._read_element(ObjectIdEnum.three_phase_instantaneous_voltage_l1)

        # wrapping second in a try as that's where we are seeing these
        # EOFErrors - for now want to make them warnings rather than fail
        #   but they do need fixing eventually
        try:
            vl2 = self._read_element(ObjectIdEnum.three_phase_instantaneous_voltage_l2)
        except EmliteEOFError as e:
            self.log.warn(f"3p v2 failed - setting to None (e={e})")
            vl2 = None

        # wrapping the third as well as now that second errors are handled
        # errors may occur on the third
        try:
            vl3 = self._read_element(ObjectIdEnum.three_phase_instantaneous_voltage_l3)
        except EmliteEOFError as e:
            self.log.warn(f"3p v3 failed - setting to None (e={e})")
            vl3 = None

        voltage_3p_tuple = (
            cast(float, vl1.voltage) / 10.0,
            None if vl2 is None else cast(float, vl2.voltage) / 10.0,
            None if vl3 is None else cast(float, vl3.voltage) / 10.0,
        )

        self.log.info(f"voltages [{voltage_3p_tuple}]")

        return voltage_3p_tuple

    def three_phase_hardware_configuration(
        self,
    ) -> EmopMessage.ThreePhaseHardwareConfigurationRec:
        data = self._read_element(ObjectIdEnum.three_phase_hardware_configuration)
        self.log.info("three phase hardware configuration", value=str(data))
        return data

    def profile_log_1(self, timestamp: datetime.datetime) -> EmopProfileLog1Response:
        log_rsp = self._profile_log(timestamp, EmopData.RecordFormat.profile_log_1)
        log_decoded = emop_decode_profile_log_1_response(log_rsp)
        self.log.debug(f"profile_log_1 response [{str(log_decoded)}]")
        return log_decoded

    def profile_log_2(self, timestamp: datetime.datetime) -> EmopProfileLog2Response:
        log_rsp = self._profile_log(timestamp, EmopData.RecordFormat.profile_log_2)

        hardware = self.hardware()
        is_twin_element = hardware == "C1.w"
        log_decoded = emop_decode_profile_log_2_response(is_twin_element, log_rsp)
        self.log.debug(
            f"profile_log_2 response [{str(log_decoded)}]",
            is_twin_element=is_twin_element,
        )

        return log_decoded

    def _profile_log(
        self, timestamp: datetime.datetime, format: EmopData.RecordFormat
    ) -> bytes:
        message_len = 4  # profile log request: timestamp (4)

        message_field = EmopProfileLogRequest()
        message_field.timestamp = emop_datetime_to_epoch_seconds(timestamp)

        _io = KaitaiStream(BytesIO(bytearray(message_len)))
        message_field._write(_io)
        message_field_bytes = _io.to_byte_array()

        data_field = EmopData(message_len)
        data_field.format = format
        data_field.message = message_field_bytes

        _io = KaitaiStream(BytesIO(bytearray(message_len + 1)))
        data_field._write(_io)
        data_field_bytes = _io.to_byte_array()

        self.log.info(f"profile log request [{data_field_bytes.hex()}]")
        response_bytes = self._send_message(data_field_bytes)

        return response_bytes

    """
        See Section 1 of the EMP1 ax and cx Communication Protocol Specification v1_0.pdf.

        NOTE: If the start & end times are both earlier than the first available record,
              only the first record will be returned. 
              If the start & end times are both later than the last record, only the last
              record will be returned.
    """

    def three_phase_intervals(
        self,
        day: datetime.datetime,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        csv: str,
        include_statuses: bool = False,
    ) -> ThreePhaseIntervals:
        hours_per_frame = 4

        #  day given then setup start and end for it
        if day:
            start_time = datetime.datetime.combine(
                day, time(0, 0), tzinfo=ZoneInfo("UTC")
            )
            end_time = datetime.datetime.combine(
                day, time(23, 30), tzinfo=ZoneInfo("UTC")
            )

        # otherwise check start and end times
        else:
            if start_time >= end_time:
                raise Exception("start_time must come before end_time")

            # The meter can do up to 24 hours but we limit to hours_per_frame hours
            # which fits in 512 bytes that emlite_net reads from the response.
            #
            # There is no reason this can't be lifted to support 24 hours although
            # it hasn't been tried.
            #
            # For now it's up to the caller of this function to get and assemble 8
            # hour chunks at a time.
            if end_time > start_time + datetime.timedelta(hours=24):
                raise Exception("max range between start_time and end_time is 24 hours")

        hardware = self.three_phase_hardware_configuration()
        self.log.info(f"meter type = {hardware.meter_type.name}")

        # COMMENT OUT this reset for now as it crashed 2 cx meters
        #             they need a physical reset to get working again

        # self._three_phase_intervals(
        #     start_time,
        #     end_time,
        #     EmopProfileThreePhaseIntervalsRequest.ProfileNumber.reset,
        # )

        all_intervals: ThreePhaseIntervals

        # If the range is 8 hours or less, make a single call
        if end_time <= start_time + datetime.timedelta(hours=hours_per_frame):
            block = self._three_phase_intervals_read(
                start_time,
                end_time,
                EmopProfileThreePhaseIntervalsRequest.ProfileNumber.profile_0,
            )
            all_intervals = blocks_to_intervals_rec([block])
        else:
            # For ranges > 4 hours, make multiple calls
            blocks = []
            current_start = start_time

            while current_start < end_time:
                # Calculate the end time for this chunk (max hours_per_frame hours)
                current_end = min(
                    current_start + datetime.timedelta(hours=hours_per_frame), end_time
                )

                block = self._three_phase_intervals_read(
                    current_start,
                    current_end,
                    EmopProfileThreePhaseIntervalsRequest.ProfileNumber.profile_0,
                )
                blocks.append(block)

                # Move to the next chunk
                current_start = current_end

            all_intervals = blocks_to_intervals_rec(blocks)

        export_three_phase_intervals_to_csv(
            all_intervals, csv, hardware.meter_type, include_statuses
        )
        self.log.info(f"wrote intervals to [{csv}]")

        return all_intervals

    def event_log(self, log_idx: int) -> EmopEventLogResponse:
        message_len = 4  # object id (3) + log_idx (1)

        message_field = EmopEventLogRequest()
        message_field.object_id = emop_encode_object_id(
            EmopMessage.ObjectIdType.event_log
        )
        message_field.log_idx = log_idx

        _io = KaitaiStream(BytesIO(bytearray(message_len)))
        message_field._write(_io)
        message_field_bytes = _io.to_byte_array()

        data_field = EmopData(message_len)
        data_field.format = EmopData.RecordFormat.event_log
        data_field.message = message_field_bytes

        _io = KaitaiStream(BytesIO(bytearray(message_len + 1)))
        data_field._write(_io)
        data_field_bytes = _io.to_byte_array()

        self.log.info(f"event log request [{data_field_bytes.hex()}]")
        response_bytes = self._send_message(data_field_bytes)
        self.log.info(f"event log response [{response_bytes.hex()}]")

        data = EmopEventLogResponse(KaitaiStream(BytesIO(response_bytes)))
        data._read()
        self.log.info(f"event logs [{data}]")

        return data

    def tariffs_active_read(self) -> TariffsActive:
        standing_charge_rec = self._read_element(
            ObjectIdEnum.tariff_active_standing_charge
        )
        self.log.debug("standing charge", value=standing_charge_rec.value)

        threshold_mask_rec: EmopMessage.TariffThresholdMaskRec = self._read_element(
            ObjectIdEnum.tariff_active_threshold_mask
        )
        threshold_values_rec = self._read_element(
            ObjectIdEnum.tariff_active_threshold_values
        )
        self._log_thresholds(threshold_mask_rec, threshold_values_rec)

        block_8_rate_1_price_rec = self._read_element(
            ObjectIdEnum.tariff_active_block_8_rate_1
        )
        self.log.debug(
            "block 8 rate 1 (element a activated rate)",
            value=emop_scale_price_amount(block_8_rate_1_price_rec.value),
        )

        active_price_rec = self._read_element(ObjectIdEnum.tariff_active_price)
        self.log.debug(
            "element a unit rate (active a price)", value=active_price_rec.value
        )

        block_rate_rec = self._read_element(ObjectIdEnum.tariff_active_block_rate)
        self.log.debug("element a block rate index (0-7)", value=block_rate_rec.value)

        tou_rate_index_rec = self._read_element(ObjectIdEnum.tariff_active_tou_rate)
        self.log.debug("element a tou rate index (0-7)", value=tou_rate_index_rec.value)

        # price_index_rec = self._read_element(
        #     ObjectIdEnum.tariff_active_price_index_current
        # )
        # self.log.debug("price index (0-63)", value=price_index_rec.value)

        element_b_price_rec = self._read_element(
            ObjectIdEnum.tariff_active_element_b_price
        )
        self.log.debug(
            "element b unit rate (active b price)", value=element_b_price_rec.value
        )

        element_b_tou_rate_rec = self._read_element(
            ObjectIdEnum.tariff_active_element_b_tou_rate
        )
        self.log.debug(
            "element b tou rate index (0-3)", value=element_b_tou_rate_rec.value
        )

        # element_b_tou_rate_1_rec = self._read_element(
        #     ObjectIdEnum.tariff_active_element_b_tou_rate_1
        # )
        # self.log.debug("element b tou rate price 1", value=element_b_tou_rate_1_rec.value)

        # element_b_price_index_rec = self._read_element(
        #     ObjectIdEnum.tariff_active_element_b_price_index_current
        # )
        # self.log.debug("element b price index", value=element_b_price_index_rec.value)

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

        # pricing_table = []
        # self._tariffs_pricing_blocks_read(True)
        # self.log.debug("pricing table", pricing_table=pricing_table)

        tariffs = TariffsActive(
            standing_charge=str(emop_scale_price_amount(standing_charge_rec.value)),
            threshold_mask=self._pluck_keys(threshold_mask_rec, "rate"),
            threshold_values=self._pluck_keys(threshold_values_rec, "th"),
            unit_rate_element_a=str(emop_scale_price_amount(active_price_rec.value)),
            unit_rate_element_b=str(emop_scale_price_amount(element_b_price_rec.value)),
            prepayment_debt_recovery_rate=str(
                emop_scale_price_amount(debt_recovery_rec.value)
            ),
            prepayment_ecredit_availability=str(
                emop_scale_price_amount(ecredit_rec.value)
            ),
            prepayment_emergency_credit=str(
                emop_scale_price_amount(emergency_credit_rec.value)
            ),
            block_rate=block_rate_rec.value,
            tou_rate=None,
            price_current=None,
            element_b_tou_rate=element_b_tou_rate_rec.value,
            # not fetched and set:
            element_b_block_rate=None,
            element_b_tou_rate_1=None,
            element_b_tou_rate_2=None,
            element_b_tou_rate_3=None,
            element_b_tou_rate_4=None,
            element_b_price_index_current=None,
            price_index_current=None,
            pricings=None,
            gas=None,
        )

        self.log.info("active tariffs", result=tariffs)

        return tariffs

    def tariffs_future_read(self) -> TariffsFuture:
        standing_charge_rec = self._read_element(
            ObjectIdEnum.tariff_future_standing_charge
        )
        self.log.debug("standing charge", value=standing_charge_rec.value)

        activation_timestamp_rec = self._read_element(
            ObjectIdEnum.tariff_future_activation_datetime
        )
        self.log.debug("activation timestamp", value=activation_timestamp_rec.value)

        threshold_mask_rec = self._read_element(
            ObjectIdEnum.tariff_future_threshold_mask
        )
        threshold_values_rec = self._read_element(
            ObjectIdEnum.tariff_future_threshold_values
        )
        self._log_thresholds(threshold_mask_rec, threshold_values_rec)

        block_8_rate_1_rec = self._read_element(
            ObjectIdEnum.tariff_future_block_8_rate_1
        )
        self.log.debug(
            "unit_rate_element_a (set on block 8, rate 1)",
            value=block_8_rate_1_rec.value,
        )

        element_b_tou_rate_1_rec = self._read_element(
            ObjectIdEnum.tariff_future_element_b_tou_rate_1
        )
        self.log.debug(
            "unit_rate_element_b (set on tou rate 1)",
            value=element_b_tou_rate_1_rec.value,
        )

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

        # pricing_table = self._tariffs_pricing_blocks_read(False)
        # self.log.debug("pricing_table", pricing_table=pricing_table)

        tariffs = TariffsFuture(
            standing_charge=str(emop_scale_price_amount(standing_charge_rec.value)),
            activation_datetime=emop_epoch_seconds_to_datetime(
                activation_timestamp_rec.value
            )
            # TODO set timezone that works for BST and winter. is this it?
            # .replace(tzinfo=ZoneInfo("Europe/London"))
            .isoformat(timespec="seconds"),
            threshold_mask=self._pluck_keys(threshold_mask_rec, "rate"),
            threshold_values=self._pluck_keys(threshold_values_rec, "th"),
            unit_rate_element_a=str(emop_scale_price_amount(block_8_rate_1_rec.value)),
            unit_rate_element_b=str(
                emop_scale_price_amount(element_b_tou_rate_1_rec.value)
            ),
            prepayment_debt_recovery_rate=str(
                emop_scale_price_amount(debt_recovery_rec.value)
            ),
            prepayment_ecredit_availability=str(
                emop_scale_price_amount(ecredit_rec.value)
            ),
            prepayment_emergency_credit=str(
                emop_scale_price_amount(emergency_credit_rec.value)
            ),
            pricings=None,
            element_b_tou_rate_1=None,
            element_b_tou_rate_2=None,
            element_b_tou_rate_3=None,
            element_b_tou_rate_4=None,
        )

        self.log.info("future tariffs", result=tariffs)

        return tariffs

    def tariffs_future_write(
        self,
        from_ts: datetime.datetime,
        standing_charge: Decimal,
        unit_rate: Decimal,
        emergency_credit: Decimal,
        ecredit_availability: Decimal,
        debt_recovery_rate: Decimal,
    ) -> None:
        # block threshold mask and values - set values to zeros and rate 1 only in mask
        threshold_mask_bytes = bytes(1)
        self.log.debug("zero out threshold mask")
        self._write_element(
            ObjectIdEnum.tariff_future_threshold_mask, threshold_mask_bytes
        )

        threshold_values_bytes = bytes(14)
        self.log.debug("zero out threshold values")
        self._write_element(
            ObjectIdEnum.tariff_future_threshold_values, threshold_values_bytes
        )

        # TOU and rates
        # - turn flag off
        # - set A element block 8 / rate 1 - only this is needed
        # - set B element rate 1 to the single fixed rate - only this is needed
        self.log.debug("switch off tou flag")
        self._write_element(ObjectIdEnum.tariff_future_tou_flag, bytes(1))

        unit_rate_encoded = emop_encode_amount_as_u4le_rec(unit_rate)

        self.log.debug(f"set element a unit rate (on block 8, rate 1) to {unit_rate}")
        self._write_element(
            ObjectIdEnum.tariff_future_block_8_rate_1, unit_rate_encoded
        )

        self.log.debug(f"set element b unit rate (on tou rate 1) to {unit_rate}")
        self._write_element(
            ObjectIdEnum.tariff_future_element_b_tou_rate_1, unit_rate_encoded
        )

        # NOTE: following unncessary as we just activate rate 1 but left in
        # here for future in case we use it

        # self._write_element(
        #     ObjectIdEnum.tariff_future_element_b_tou_rate_2, unit_rate_encoded
        # )
        # self._write_element(
        #     ObjectIdEnum.tariff_future_element_b_tou_rate_3, unit_rate_encoded
        # )
        # self._write_element(
        #     ObjectIdEnum.tariff_future_element_b_tou_rate_4, unit_rate_encoded
        # )

        # prepayment amounts
        self.log.debug(
            f"set prepayment amounts [emergency_credit={emergency_credit}, ecredit_availability={ecredit_availability}, debt_recovery_rate={debt_recovery_rate}]"
        )
        self._write_element(
            ObjectIdEnum.tariff_future_prepayment_emergency_credit,
            emop_encode_amount_as_u4le_rec(emergency_credit),
        )
        self._write_element(
            ObjectIdEnum.tariff_future_prepayment_ecredit_availability,
            emop_encode_amount_as_u4le_rec(ecredit_availability),
        )
        self._write_element(
            ObjectIdEnum.tariff_future_prepayment_debt_recovery_rate,
            emop_encode_amount_as_u4le_rec(debt_recovery_rate),
        )

        # gas tariff - set to zero as it doesn't apply
        self.log.debug("set gas rate to zero")
        self._write_element(ObjectIdEnum.tariff_future_gas, bytes(4))

        # set all the other block / units to zero
        # NOTE: typically unncessary as we only need to activate block 8 / rate 1
        #       but left in here if it's required in future

        # zero_rate_bytes = bytes(4)
        # for block in range(1, 9):
        #     for rate in range(1, 9):
        #         if block == 8 and rate == 1:
        #             continue
        #         object_id_str = f"tariff_future_block_{block}_rate_{rate}"
        #         self._write_element(ObjectIdEnum[object_id_str], zero_rate_bytes)
        #         self.log.debug(f"{object_id_str} set to zero")

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

    def tariffs_time_switches_element_a_or_single_read(self) -> bytes:
        data = self._read_element(ObjectIdEnum.tariff_time_switch_element_a_or_single)
        self.log.info("element A switch settings", value=data.switch_settings)
        return cast(bytes, data.switch_settings)

    def tariffs_time_switches_element_a_or_single_write(self) -> None:
        self._tariffs_time_switches_write(
            ObjectIdEnum.tariff_time_switch_element_a_or_single
        )

    def tariffs_time_switches_element_b_read(self) -> bytes:
        data = self._read_element(ObjectIdEnum.tariff_time_switch_element_b)
        self.log.info("element B switch settings", value=data.switch_settings)
        return cast(bytes, data.switch_settings)

    def tariffs_time_switches_element_b_write(self) -> None:
        self._tariffs_time_switches_write(ObjectIdEnum.tariff_time_switch_element_b)

    def _tariffs_time_switches_write(self, object_id: ObjectIdEnum) -> None:
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

    def obis_read(self, obis: str) -> bytes:
        object_id = emop_obis_triplet_to_decimal(obis)
        result = self._read_element(object_id)
        self.log.info("obis_read", obis=obis, result=result.payload.hex())
        return cast(bytes, result.payload)

    def obis_write(self, obis: str, payload_hex: str) -> None:
        object_id = emop_obis_triplet_to_decimal(obis)
        payload_bytes = bytes.fromhex(payload_hex)
        self._write_element(object_id, payload_bytes)

    def _read_element(self, object_id: ObjectIdEnum | int) -> Any:
        try:
            data = self.grpc_client.read_element(object_id)
        except EmliteConnectionFailure as e:
            raise MediatorClientException("EMLITE_CONNECTION_FAILURE", e.message)
        except EmliteEOFError as e:
            raise MediatorClientException("EMLITE_EOF_ERROR", e.message)
        except grpc.RpcError as e:
            raise MediatorClientException(e.code().name, e.details())
        return data

    def _write_element(self, object_id: ObjectIdEnum | int, payload: bytes) -> None:
        try:
            self.grpc_client.write_element(object_id, payload)
        except EmliteConnectionFailure as e:
            raise MediatorClientException("EMLITE_CONNECTION_FAILURE", e.message)
        except EmliteEOFError as e:
            raise MediatorClientException("EMLITE_EOF_ERROR", e.message)
        except grpc.RpcError as e:
            raise MediatorClientException(e.code().name, e.details())

    def _send_message(self, message: bytes) -> bytes:
        try:
            data = self.grpc_client.send_message(message)
        except grpc.RpcError as e:
            raise MediatorClientException(e.code().name, e.details())
        return data

    def _log_thresholds(
        self,
        threshold_mask: EmopMessage.TariffThresholdMaskRec,
        threshold_values: EmopMessage.TariffThresholdValuesRec,
    ) -> None:
        self.log.info(
            f"threshold mask [1={threshold_mask.rate1} 2={threshold_mask.rate2} 3={threshold_mask.rate3} 4={threshold_mask.rate4} 5={threshold_mask.rate5} 6={threshold_mask.rate6} 7={threshold_mask.rate7} 8={threshold_mask.rate8}]"
        )
        self.log.info(
            f"threshold values [1={threshold_values.th1} 2={threshold_values.th2} 3={threshold_values.th3} 4={threshold_values.th4} 5={threshold_values.th5} 6={threshold_values.th6} 7={threshold_values.th7}]"
        )

    def _pluck_keys(
        self,
        rec: EmopMessage.TariffThresholdMaskRec | EmopMessage.TariffThresholdValuesRec,
        key_prefix: str,
    ) -> Dict[str, Any]:
        return {k: v for k, v in vars(rec).items() if k.startswith(key_prefix)}

    def _three_phase_intervals_read(
        self,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        profile: EmopProfileThreePhaseIntervalsRequest.ProfileNumber,
    ) -> EmopProfileThreePhaseIntervalsResponseBlock | None:
        message_len = 13  # profile number + 2 x 4 byte timestamp + 4 bytes fixed)

        message_field = EmopProfileThreePhaseIntervalsRequest()
        message_field.profile_number = profile
        message_field.start_time = emop_datetime_to_epoch_seconds(start_time)
        message_field.end_time = emop_datetime_to_epoch_seconds(end_time)
        message_field.trailing_fixed = bytearray.fromhex("ffffffff")

        _io = KaitaiStream(BytesIO(bytearray(message_len)))
        message_field._write(_io)
        message_field_bytes = _io.to_byte_array()

        data_field = EmopData(message_len)
        data_field.format = EmopData.RecordFormat.three_phase_profile_intervals
        data_field.message = message_field_bytes

        _io = KaitaiStream(BytesIO(bytearray(message_len + 1)))
        data_field._write(_io)
        data_field_bytes = _io.to_byte_array()

        self.log.debug(
            f"three phase intervals frame request [{data_field_bytes.hex()}]"
        )
        response_bytes = self._send_message(data_field_bytes)
        self.log.debug(f"three phase intervals frame response [{response_bytes.hex()}]")

        if profile == EmopProfileThreePhaseIntervalsRequest.ProfileNumber.reset:
            return None

        frame = EmopProfileThreePhaseIntervalsResponseFrame(
            len(response_bytes), KaitaiStream(BytesIO(response_bytes))
        )
        frame._read()
        self.log.debug(f"three phase intervals frame [{str(frame)}]")

        block = EmopProfileThreePhaseIntervalsResponseBlock(
            len(frame.frame_data), KaitaiStream(BytesIO(frame.frame_data))
        )
        block._read()
        self.log.debug(f"three phase intervals block [{str(block)}]")

        return block

    def _safe_read_element(self, element_id):
        """Safely read an element, returning None if it fails."""
        try:
            return self._read_element(element_id)
        except Exception as e:
            element_name = getattr(element_id, "name", str(element_id))
            logger.error(f"Failed to read element {element_name}. Exception: {e}")
            return None

    def _scale_kilo_value(self, rec: EmopMessage.U4leValueRec | None):
        return rec.value / 1000 if rec else None
