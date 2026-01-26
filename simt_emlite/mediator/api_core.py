# mypy: disable-error-code="import-untyped"
"""
Core API for Emlite meter operations.

This module provides the main API for reading meter data, managing settings,
and performing core operations. Prepay and tariff-related operations are in
api_prepay.py.
"""
import datetime
import logging
from typing import Any, Dict, Tuple, cast
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
    emop_encode_datetime_to_time_rec,
    emop_encode_object_id,
    emop_format_firmware_version,
    emop_obis_triplet_to_decimal,
)
from emop_frame_protocol.vendor.kaitaistruct import BytesIO, KaitaiStream

from simt_emlite.dto.three_phase_intervals import ThreePhaseIntervals
from simt_emlite.mediator.grpc.exception.EmliteConnectionFailure import (
    EmliteConnectionFailure,
)
from simt_emlite.mediator.grpc.exception.EmliteEOFError import EmliteEOFError
from simt_emlite.util.logging import get_logger
from simt_emlite.util.meters import (
    is_three_phase,
    is_twin_element,
    single_phase_hardware_str_to_registry_str,
)
from simt_emlite.util.three_phase_intervals import (
    blocks_to_intervals_rec,
    export_three_phase_intervals_to_csv,
)

from .grpc.client import EmliteMediatorGrpcClient
from .mediator_client_exception import MediatorClientException
from .validation import valid_event_log_idx

logger = get_logger(__name__, __file__)


class EmliteMediatorAPI(object):
    """
    Core API client for Emlite meter operations.

    This class provides methods for reading meter data, managing settings,
    and performing core meter operations. For prepay and tariff operations,
    use EmlitePrepayAPI from api_prepay.py.
    """

    def __init__(
        self,
        mediator_address: str | None = "0.0.0.0:50051",
        logging_level: str | int = logging.INFO,
    ) -> None:
        self.grpc_client = EmliteMediatorGrpcClient(
            mediator_address=mediator_address,
        )

        logging.getLogger().setLevel(logging_level)

        global logger
        self.log = logger.bind(mediator_address=mediator_address)
        self.log.debug("EmliteMediatorClient init")
        self._hardware_cache: Dict[str, str] = {}

    def get_info(self, serial: str) -> str:
        data = self.grpc_client.get_info(serial)
        self.log.info("received info", serial=serial)
        return data

    def get_meters(self) -> str:
        data = self.grpc_client.get_meters()
        self.log.info("received meters list")
        return data

    def serial_read(self, serial: str) -> str:
        data = self._read_element(serial, ObjectIdEnum.serial)
        serial_resp: str = data.serial.strip()
        self.log.info("received serial", serial=serial_resp, request_serial=serial)
        return serial_resp

    def hardware(self, serial: str) -> str:
        if serial in self._hardware_cache:
            return self._hardware_cache[serial]

        data = self._read_element(serial, ObjectIdEnum.hardware_version)

        # if blank then it's a three phase meter
        if data.hardware == "":
            config = self.three_phase_hardware_configuration(serial)
            if config.meter_type == EmopMessage.ThreePhaseMeterType.ax_whole_current:
                hardware = "P1.ax"
            elif config.meter_type == EmopMessage.ThreePhaseMeterType.cx_ct_operated:
                hardware = "P1.cx"
            else:
                hardware = "THREE_PHASE_UNKNOWN"
        else:
            hardware_clean: str = data.hardware.replace("\u0000", "").strip()
            hardware_optional: str | None = (
                single_phase_hardware_str_to_registry_str.get(hardware_clean, None)
            )
            if hardware_optional is None:
                hardware = "SINGLE_PHASE_UNKNOWN"
            else:
                hardware = hardware_optional

        self.log.info("hardware", hardware=hardware, serial=serial)
        self._hardware_cache[serial] = hardware

        return hardware

    def firmware_version(self, serial: str) -> str:
        data = self._read_element(serial, ObjectIdEnum.firmware_version)
        version_bytes = bytearray(data.version_bytes)
        if len(version_bytes) == 4:
            # single phase meter
            version_str = emop_format_firmware_version(version_bytes.decode("ASCII"))
        else:
            # three phase meter
            version_str = version_bytes.hex()
        self.log.info("firmware version", firmware_version=version_str, serial=serial)
        return str(version_str)

    def clock_time_read(self, serial: str) -> datetime.datetime:
        data = self._read_element(serial, ObjectIdEnum.time)
        date_obj = datetime.datetime(
            2000 + data.year,
            data.month,
            data.date,
            data.hour,
            data.minute,
            data.second,
            tzinfo=datetime.timezone.utc,
        )
        self.log.info("received time", time=date_obj.isoformat(), serial=serial)
        return date_obj

    def clock_time_write(self, serial: str) -> None:
        time_bytes = emop_encode_datetime_to_time_rec(
            datetime.datetime.now(tz=datetime.timezone.utc)
        )
        self._write_element(serial, ObjectIdEnum.time, time_bytes)

    def csq(self, serial: str) -> int:
        data = self._read_element(serial, ObjectIdEnum.csq_net_op)
        self.log.info("received csq", csq=data.csq, serial=serial)
        return cast(int, data.csq)

    def instantaneous_voltage(self, serial: str) -> float:
        data = self._read_element(serial, ObjectIdEnum.instantaneous_voltage)
        self.log.info(
            "received instantaneous voltage", voltage=data.voltage, serial=serial
        )
        return float(data.voltage)

    def instantaneous_active_power(self, serial: str) -> float:
        data = self._read_element(serial, ObjectIdEnum.instantaneous_active_power)
        power_kwh = data.power / 1000
        self.log.info(
            "received instantaneous active power", power_kwh=power_kwh, serial=serial
        )
        return float(power_kwh)

    def instantaneous_active_power_element_a(self, serial: str) -> float:
        data = self._read_element(
            serial, ObjectIdEnum.element_a_instantaneous_active_power_import
        )
        power_kwh = data.power / 1000
        self.log.info(
            "received instantaneous active power (element a)",
            power_kwh=power_kwh,
            serial=serial,
        )
        return float(power_kwh)

    def instantaneous_active_power_element_b(self, serial: str) -> float:
        data = self._read_element(
            serial, ObjectIdEnum.element_b_instantaneous_active_power_import
        )
        power_kwh = data.power / 1000
        self.log.info(
            "received instantaneous active power (element b)",
            power_kwh=power_kwh,
            serial=serial,
        )
        return float(power_kwh)

    def read(
        self, serial: str
    ) -> Tuple[Dict[str, float], Dict[str, float] | None] | Dict[str, float | None]:
        hardware = self.hardware(serial)
        is_3p = is_three_phase(hardware)
        if is_3p:
            return self.three_phase_read(serial, hardware)
        else:
            element_a: Dict[str, float] = self.read_element_a(serial)
            element_b: Dict[str, float] | None = None
            if is_twin_element(hardware):
                element_b = self.read_element_b(serial)
            single_phase_reads = (element_a, element_b)
            self.log.info(f"single phase read [{single_phase_reads}]", serial=serial)
            return single_phase_reads

    def read_element_a(self, serial: str) -> Dict[str, float]:
        data = self._read_element(serial, ObjectIdEnum.read_element_a)
        reads = {
            "import_active": data.import_active / 1000,
            "export_active": data.export_active / 1000,
            "import_reactive": data.import_reactive / 1000,
            "export_reactive": data.export_reactive / 1000,
        }
        self.log.info("received read_element_a record", reads=reads, serial=serial)
        return reads

    def read_element_b(self, serial: str) -> Dict[str, float]:
        data = self._read_element(serial, ObjectIdEnum.read_element_b)
        reads = {
            "import_active": data.import_active / 1000,
            "export_active": data.export_active / 1000,
            "import_reactive": data.import_reactive / 1000,
            "export_reactive": data.export_reactive / 1000,
        }
        self.log.info("received read_element_b record", reads=reads, serial=serial)
        return reads

    def daylight_savings_correction_enabled(self, serial: str) -> bool:
        data = self._read_element(serial, ObjectIdEnum.daylight_savings_correction_flag)
        enabled: bool = data.enabled_flag == 1
        self.log.info(
            "received daylight savings correction flag",
            daylight_savings_correction_flag=enabled,
            serial=serial,
        )
        return enabled

    def daylight_savings_correction_enabled_write(
        self, serial: str, enabled: bool
    ) -> None:
        flag_bytes = bytes.fromhex("01" if enabled else "00")
        self._write_element(
            serial, ObjectIdEnum.daylight_savings_correction_flag, flag_bytes
        )

    def backlight(self, serial: str) -> EmopMessage.BacklightSettingType:
        data = self._read_element(serial, ObjectIdEnum.backlight)
        self.log.info(
            "received backlight setting", backlight_setting=data.setting, serial=serial
        )
        return data.setting

    def backlight_write(
        self, serial: str, setting: EmopMessage.BacklightSettingType
    ) -> None:
        setting_bytes = bytes([setting.value])
        self._write_element(serial, ObjectIdEnum.backlight, setting_bytes)

    def load_switch(self, serial: str) -> EmopMessage.LoadSwitchSettingType:
        data = self._read_element(serial, ObjectIdEnum.load_switch)
        self.log.info(
            "received load switch setting",
            load_switch_setting=data.setting,
            serial=serial,
        )
        return data.setting

    def load_switch_write(
        self, serial: str, setting: EmopMessage.LoadSwitchSettingType
    ) -> None:
        setting_bytes = bytes([setting.value])
        self._write_element(serial, ObjectIdEnum.load_switch, setting_bytes)

    def three_phase_serial(self, serial: str) -> str:
        data = self._read_element(serial, ObjectIdEnum.three_phase_serial)
        serial_resp = data.serial.strip()
        self.log.info(
            "received three phase serial", serial=serial_resp, request_serial=serial
        )
        return cast(str, serial_resp)

    def three_phase_read(
        self, serial: str, hardware: str | None
    ) -> Dict[str, float | None]:
        if not hardware:
            hardware = self.hardware(serial)

        active_import: EmopMessage.U4leValueRec | None = self._safe_read_element(
            serial, ObjectIdEnum.three_phase_total_active_import
        )
        active_export: EmopMessage.U4leValueRec | None = self._safe_read_element(
            serial, ObjectIdEnum.three_phase_total_active_export
        )
        reactive_import: EmopMessage.U4leValueRec | None = self._safe_read_element(
            serial, ObjectIdEnum.three_phase_total_reactive_import
        )
        reactive_export: EmopMessage.U4leValueRec | None = self._safe_read_element(
            serial, ObjectIdEnum.three_phase_total_reactive_export
        )
        apparent_import: EmopMessage.U4leValueRec | None = self._safe_read_element(
            serial, ObjectIdEnum.three_phase_total_apparent_import
        )
        apparent_export: EmopMessage.U4leValueRec | None = self._safe_read_element(
            serial, ObjectIdEnum.three_phase_total_apparent_export
        )

        reads_dict: Dict[str, float | None] = {
            "active_import": self._scale_value(active_import, hardware),
            "active_export": self._scale_value(active_export, hardware),
            "reactive_import": self._scale_value(reactive_import, hardware),
            "reactive_export": self._scale_value(reactive_export, hardware),
            "apparent_import": self._scale_value(apparent_import, hardware),
            "apparent_export": self._scale_value(apparent_export, hardware),
        }

        self.log.info(f"reads: {reads_dict}", serial=serial)

        return reads_dict

    def three_phase_instantaneous_voltage(
        self, serial: str
    ) -> tuple[float, float | None, float | None]:
        vl1 = self._read_element(
            serial, ObjectIdEnum.three_phase_instantaneous_voltage_l1
        )

        # wrapping second in a try as that's where we are seeing these
        # EOFErrors - for now want to make them warnings rather than fail
        #   but they do need fixing eventually
        try:
            vl2 = self._read_element(
                serial, ObjectIdEnum.three_phase_instantaneous_voltage_l2
            )
        except EmliteEOFError as e:
            self.log.warn(f"3p v2 failed - setting to None (e={e})", serial=serial)
            vl2 = None

        # wrapping the third as well as now that second errors are handled
        # errors may occur on the third
        try:
            vl3 = self._read_element(
                serial, ObjectIdEnum.three_phase_instantaneous_voltage_l3
            )
        except EmliteEOFError as e:
            self.log.warn(f"3p v3 failed - setting to None (e={e})", serial=serial)
            vl3 = None

        voltage_3p_tuple = (
            cast(float, vl1.voltage) / 10.0,
            None if vl2 is None else cast(float, vl2.voltage) / 10.0,
            None if vl3 is None else cast(float, vl3.voltage) / 10.0,
        )

        self.log.info(f"voltages [{voltage_3p_tuple}]", serial=serial)

        return voltage_3p_tuple

    def three_phase_hardware_configuration(
        self, serial: str
    ) -> EmopMessage.ThreePhaseHardwareConfigurationRec:
        data = self._read_element(
            serial, ObjectIdEnum.three_phase_hardware_configuration
        )
        self.log.info(
            "three phase hardware configuration", value=str(data), serial=serial
        )
        return data

    def profile_log_1(
        self, serial: str, timestamp: datetime.datetime
    ) -> EmopProfileLog1Response:
        log_rsp = self._profile_log(
            serial, timestamp, EmopData.RecordFormat.profile_log_1
        )
        log_decoded: EmopProfileLog1Response = emop_decode_profile_log_1_response(
            log_rsp
        )
        self.log.info(f"profile_log_1 response [{str(log_decoded)}]", serial=serial)
        return log_decoded

    def profile_log_2(
        self, serial: str, timestamp: datetime.datetime, is_twin_element: bool
    ) -> EmopProfileLog2Response:
        log_rsp = self._profile_log(
            serial, timestamp, EmopData.RecordFormat.profile_log_2
        )

        log_decoded: EmopProfileLog2Response = emop_decode_profile_log_2_response(
            is_twin_element, log_rsp
        )
        self.log.info(
            f"profile_log_2 response [{str(log_decoded)}]",
            is_twin_element=is_twin_element,
            serial=serial,
        )

        return log_decoded

    def _profile_log(
        self, serial: str, timestamp: datetime.datetime, format: EmopData.RecordFormat
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

        self.log.info(f"profile log request [{data_field_bytes.hex()}]", serial=serial)
        response_bytes = self._send_message(serial, data_field_bytes)

        return response_bytes

    def three_phase_intervals(
        self,
        serial: str,
        day: datetime.datetime | None,
        start_time: datetime.datetime | None,
        end_time: datetime.datetime | None,
        csv: str | None = None,
        include_statuses: bool = False,
    ) -> ThreePhaseIntervals:
        hours_per_frame = 4

        #  day given then setup start and end for it
        if day:
            start_time = datetime.datetime.combine(
                day, datetime.time(0, 0), tzinfo=ZoneInfo("UTC")
            )
            end_time = datetime.datetime.combine(
                day, datetime.time(23, 30), tzinfo=ZoneInfo("UTC")
            )

        # otherwise check start and end times
        else:
            if start_time is None or end_time is None:
                raise Exception("start_time and end_time must be provided")

            if start_time >= end_time:
                raise Exception("start_time must come before end_time")

            if end_time > start_time + datetime.timedelta(hours=24):
                raise Exception("max range between start_time and end_time is 24 hours")

        hardware = self.three_phase_hardware_configuration(serial)
        self.log.info(f"meter type = {hardware.meter_type.name}", serial=serial)

        all_intervals: ThreePhaseIntervals

        # If the range is 8 hours or less, make a single call
        if end_time <= start_time + datetime.timedelta(hours=hours_per_frame):
            block = self._three_phase_intervals_read(
                serial,
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
                    serial,
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
        if csv:
            self.log.info(f"wrote intervals to [{csv}]", serial=serial)
        else:
            self.log.info("wrote intervals to stdout", serial=serial)

        return all_intervals

    def event_log(self, serial: str, log_idx: int) -> EmopEventLogResponse:
        valid_event_log_idx(log_idx)
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

        self.log.info(f"event log request [{data_field_bytes.hex()}]", serial=serial)
        response_bytes = self._send_message(serial, data_field_bytes)
        self.log.info(f"event log response [{response_bytes.hex()}]", serial=serial)

        data = EmopEventLogResponse(KaitaiStream(BytesIO(response_bytes)))
        data._read()
        self.log.info(f"event logs [{data}]", serial=serial)

        return data

    def obis_read(self, serial: str, obis: str) -> bytes:
        object_id = emop_obis_triplet_to_decimal(obis)
        result = self._read_element(serial, object_id)
        self.log.info(
            "obis_read", obis=obis, result=result.payload.hex(), serial=serial
        )
        return cast(bytes, result.payload)

    def obis_write(self, serial: str, obis: str, payload_hex: str) -> None:
        object_id = emop_obis_triplet_to_decimal(obis)
        payload_bytes = bytes.fromhex(payload_hex)
        self._write_element(serial, object_id, payload_bytes)

    def _read_element(self, serial: str, object_id: ObjectIdEnum | int) -> Any:
        try:
            data = self.grpc_client.read_element(serial, object_id)
        except EmliteConnectionFailure as e:
            raise MediatorClientException("EMLITE_CONNECTION_FAILURE", e.message)
        except EmliteEOFError as e:
            raise MediatorClientException("EMLITE_EOF_ERROR", e.message)
        except grpc.RpcError as e:
            raise MediatorClientException(e.code().name, str(e.details() or ""))
        return data

    def _write_element(
        self, serial: str, object_id: ObjectIdEnum | int, payload: bytes
    ) -> None:
        try:
            self.grpc_client.write_element(serial, object_id, payload)
        except EmliteConnectionFailure as e:
            raise MediatorClientException("EMLITE_CONNECTION_FAILURE", e.message)
        except EmliteEOFError as e:
            raise MediatorClientException("EMLITE_EOF_ERROR", e.message)
        except grpc.RpcError as e:
            raise MediatorClientException(e.code().name, str(e.details() or ""))

    def _send_message(self, serial: str, message: bytes) -> bytes:
        try:
            data = self.grpc_client.send_message(serial, message)
        except grpc.RpcError as e:
            raise MediatorClientException(e.code().name, str(e.details() or ""))
        return data

    def _three_phase_intervals_read(
        self,
        serial: str,
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
            f"three phase intervals frame request [{data_field_bytes.hex()}]",
            serial=serial,
        )
        response_bytes = self._send_message(serial, data_field_bytes)
        self.log.debug(
            f"three phase intervals frame response [{response_bytes.hex()}]",
            serial=serial,
        )

        if profile == EmopProfileThreePhaseIntervalsRequest.ProfileNumber.reset:
            return None

        frame = EmopProfileThreePhaseIntervalsResponseFrame(
            len(response_bytes), KaitaiStream(BytesIO(response_bytes))
        )
        frame._read()
        self.log.debug(f"three phase intervals frame [{str(frame)}]", serial=serial)

        block = EmopProfileThreePhaseIntervalsResponseBlock(
            len(frame.frame_data), KaitaiStream(BytesIO(frame.frame_data))
        )
        block._read()
        self.log.debug(f"three phase intervals block [{str(block)}]", serial=serial)

        return block

    def _safe_read_element(self, serial: str, element_id: ObjectIdEnum | int) -> Any:
        """Safely read an element, returning None if it fails."""
        try:
            return self._read_element(serial, element_id)
        except Exception as e:
            element_name = getattr(element_id, "name", str(element_id))
            logger.error(
                f"Failed to read element {element_name}. Exception: {e}", serial=serial
            )
            return None

    def _scale_value(
        self, rec: EmopMessage.U4leValueRec | None, hardware: str
    ) -> float | None:
        return (
            self._scale_10k_value(rec)
            if hardware == "P1.cx"
            else self._scale_kilo_value(rec)
        )

    def _scale_10k_value(self, rec: EmopMessage.U4leValueRec | None) -> float | None:
        return rec.value / 10_000 if rec else None

    def _scale_kilo_value(self, rec: EmopMessage.U4leValueRec | None) -> float | None:
        return rec.value / 1_000 if rec else None
