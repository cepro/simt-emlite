from kaitaistruct import KaitaiStream, BytesIO
from emlite_mediator.emlite.messages.emlite_data import EmliteData
from emlite_mediator.mediator.grpc.exception.EmliteConnectionFailure import EmliteConnectionFailure
from emlite_mediator.mediator.grpc.exception.EmliteEOFError import EmliteEOFError
from emlite_mediator.util.logging import get_logger

import datetime
import grpc
import os

from emlite_mediator.emlite.messages.emlite_object_id_enum import ObjectIdEnum

from .grpc.client import EmliteMediatorGrpcClient

logger = get_logger(__name__, __file__)

"""
    Use this class to make calls to an emlite meter through a mediator server.

    This is a wrapper around the gRPC client interface to the mediator server
    providing convencience functions to request each peice of data and get
    back a meaningful typed response.
"""


class MediatorClientException(Exception):
    def __init__(self, code_str, message):
        self.code_str = code_str
        self.message = message
        super().__init__(self.message)


class EmliteMediatorClient():
    def __init__(self, host='0.0.0.0', port=51498, meter_id=None):
        self.grpc_client = EmliteMediatorGrpcClient(host, port, meter_id)
        global logger
        self.log = logger.bind(meter_id=meter_id, mediator_port=port)
        self.log.info('port', port=port)
        # self.log.debug('EmliteMediatorClient init')

    def serial(self) -> str:
        data = self._read_element(ObjectIdEnum.serial)
        serial = data.serial.strip()
        self.log.info('received serial', serial=serial)
        return serial

    def hardware(self) -> str:
        data = self._read_element(ObjectIdEnum.hardware_version)
        hardware = data.hardware.replace('\u0000', '').strip()
        self.log.info('received hardware', hardware=hardware)
        return hardware

    def clock_time(self) -> datetime:
        data = self._read_element(ObjectIdEnum.time)
        date_obj = datetime.datetime(
            2000 + data.year, data.month, data.date, data.hour, data.minute, data.second)
        self.log.info('received time', time=date_obj.isoformat())
        return date_obj

    def csq(self) -> int:
        data = self._read_element(ObjectIdEnum.csq_net_op)
        self.log.info('received csq', csq=data.csq)
        return data.csq

    def instantaneous_voltage(self) -> float:
        data = self._read_element(ObjectIdEnum.instantaneous_voltage)
        self.log.info('received instantaneous voltage', voltage=data.voltage)
        return data.voltage

    def prepay_enabled(self) -> bool:
        data = self._read_element(ObjectIdEnum.prepay_enabled_flag)
        enabled: bool = data.enabled_flag == 1
        self.log.info('received prepay enabled flag',
                      prepay_enabled_flag=enabled)
        return enabled

    def prepay_balance(self) -> float:
        data = self._read_element(ObjectIdEnum.prepay_balance)
        self.log.debug('received prepay balance',
                       prepay_balance_raw=data.balance)
        balance_gbp: float = data.balance / 100000
        self.log.info('prepay balance in GBP', prepay_balance_gbp=balance_gbp)
        return balance_gbp

    def prepay_send_token(self, token: str):
        token_bytes = token.encode('ascii')

        # assemble the request payload manually
        data_rec_length = 5 + len(token_bytes)
        data_rec = EmliteData(data_rec_length)

        data_rec.format = b'\x01'
        data_rec.object_id = ObjectIdEnum.prepay_token_send.value.to_bytes(
            3, byteorder='big')
        data_rec.read_write = EmliteData.ReadWriteFlags.write
        data_rec.payload = token_bytes

        kt_stream = KaitaiStream(BytesIO(bytearray(data_rec_length)))
        data_rec._write(kt_stream)
        message_bytes = kt_stream.to_byte_array()

        self._send_message(message_bytes)

    def three_phase_instantaneous_voltage(self) -> tuple[float, float, float]:
        vl1 = self._read_element(
            ObjectIdEnum.three_phase_instantaneous_voltage_l1)

        # wrapping second in a try as that's where we are seeing these
        # EOFErrors - for now want to make them warnings rather than fail
        #   but they do need fixing eventually
        try:
            vl2 = self._read_element(
                ObjectIdEnum.three_phase_instantaneous_voltage_l2)
        except EmliteEOFError as e:
            self.log.warn('3p v2 failed - setting to None (e=' + e + ')')
            vl2 = None

        # wrapping the third as well as now that second errors are handled
        # errors may occur on the third
        try:
            vl3 = self._read_element(
                ObjectIdEnum.three_phase_instantaneous_voltage_l3)
        except EmliteEOFError as e:
            self.log.warn('3p v3 failed - setting to None (e=' + e + ')')
            vl3 = None

        return (
            vl1.voltage/10,
            None if vl2 is None else vl2.voltage/10,
            None if vl3 is None else vl3.voltage/10
        )

    def tariffs_read(self) -> None:
        data = self._read_element(ObjectIdEnum.tariff_active_standing_charge)
        self.log.info('standing charge', value=data.value)

        data = self._read_element(ObjectIdEnum.tariff_active_price)
        self.log.info('price', value=data.value)

        data = self._read_element(ObjectIdEnum.tariff_active_price_index)
        self.log.info('price index', value=data.value)

        data = self._read_element(ObjectIdEnum.tariff_active_tou_rate)
        self.log.info('tou rate', value=data.value)

        data = self._read_element(ObjectIdEnum.tariff_active_block_rate)
        self.log.info('block rate', value=data.value)

        data = self._read_element(ObjectIdEnum.tariff_emergency_credit)
        self.log.info('emergency credit', value=data.value)

        data = self._read_element(ObjectIdEnum.tariff_ecredit_availability)
        self.log.info('ecredit', value=data.value)

        data = self._read_element(ObjectIdEnum.tariff_debt_recovery_rate)
        self.log.info('debt recovery rate', value=data.value)

    def tariffs_time_switches_read(self) -> None:
        data = self._read_element(
            ObjectIdEnum.tariff_time_switch_element_a_or_single)
        self.log.info('el A settings bytes', value=data.switch_settings)

        data = self._read_element(
            ObjectIdEnum.tariff_time_switch_element_b)
        self.log.info('el B settings bytes', value=data.switch_settings)

    def tariffs_time_switches_element_a_or_single_write(self):
        self._tariffs_time_switches_write(
            ObjectIdEnum.tariff_time_switch_element_a_or_single)

    def tariffs_time_switches_element_b_write(self):
        self._tariffs_time_switches_write(
            ObjectIdEnum.tariff_time_switch_element_b)

    def _tariffs_time_switches_write(self, object_id: ObjectIdEnum):
        # assemble the request payload manually
        payload = bytes(80)  # all switches off - all zeros
        data_rec_length = 5 + len(payload)
        data_rec = EmliteData(data_rec_length)

        data_rec.format = b'\x01'
        data_rec.object_id = object_id.value.to_bytes(
            3, byteorder='big')
        data_rec.read_write = EmliteData.ReadWriteFlags.write
        data_rec.payload = payload

        kt_stream = KaitaiStream(BytesIO(bytearray(data_rec_length)))
        data_rec._write(kt_stream)
        message_bytes = kt_stream.to_byte_array()

        self._send_message(message_bytes)

    def _read_element(self, object_id):
        try:
            data = self.grpc_client.read_element(object_id)
        except EmliteConnectionFailure as e:
            raise MediatorClientException(
                "EMLITE_CONNECTION_FAILURE", e.message)
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


if __name__ == '__main__':
    mediator_port: str = os.environ.get("MEDIATOR_PORT")

    client = EmliteMediatorClient(port=mediator_port)
    # print(client.three_phase_instantaneous_voltage())
    # print(client.csq())

    # print(client.prepay_send_token('53251447227692530360'))
    # print(client.prepay_enabled())

    # print(client.tariffs_read())
    print(client.tariffs_time_switches_read())
