from emlite_mediator.util.logging import get_logger

import datetime
import grpc

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
    def __init__(self, host='0.0.0.0', port=50051):
        self.grpc_client = EmliteMediatorGrpcClient(host, port)
        global logger
        logger = logger.bind(host=host, port=port)
        logger.info('EmliteMediatorClient init')

    def serial(self) -> str:
        data = self._read_element(ObjectIdEnum.serial)
        serial = data.serial.strip()
        logger.info('received serial', serial=serial)
        return serial

    def hardware(self) -> str:
        data = self._read_element(ObjectIdEnum.hardware_version)
        hardware = data.hardware.replace('\u0000', '').strip()
        logger.info('received hardware', hardware=hardware)
        return hardware

    def clock_time(self) -> datetime:
        data = self._read_element(ObjectIdEnum.time)
        date_obj = datetime.datetime(
            2000 + data.year, data.month, data.date, data.hour, data.minute, data.second)
        logger.info('received time', time=date_obj.isoformat())
        return date_obj

    def csq(self) -> int:
        data = self._read_element(ObjectIdEnum.csq_net_op)
        logger.info('received csq', csq=data.csq)
        return data.csq

    def instantaneous_voltage(self) -> int:
        data = self._read_element(ObjectIdEnum.instantaneous_voltage)
        logger.info('received instantaneous voltage', voltage=data.voltage)
        return data.voltage

    def prepay_enabled(self) -> bool:
        data = self._read_element(ObjectIdEnum.prepay_enabled_flag)
        enabled: bool = data.enabled_flag == 1
        logger.info('received prepay enabled flag',
                    prepay_enabled_flag=enabled)
        return enabled

    def prepay_balance(self) -> float:
        data = self._read_element(ObjectIdEnum.prepay_balance)
        logger.debug('received prepay balance',
                     prepay_balance_raw=data.balance)
        balance_gbp: float = data.balance / 100000
        logger.info('prepay balance in GBP', prepay_balance_gbp=balance_gbp)
        return balance_gbp

    def _read_element(self, object_id):
        try:
            data = self.grpc_client.read_element(object_id)
        except grpc.RpcError as e:
            raise MediatorClientException(e.code().name, e.details())
        return data


if __name__ == '__main__':
    client = EmliteMediatorClient()
    print(client.clock_time())
    print(client.csq())
