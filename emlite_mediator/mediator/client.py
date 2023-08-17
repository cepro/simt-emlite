import datetime

import grpc

from emlite_mediator.emlite.messages.emlite_object_id_enum import ObjectIdEnum
from emlite_mediator.util.logging import get_logger

from .grpc.client import EmliteMediatorGrpcClient

logger = get_logger(__name__)

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
        logger.info('EmliteMediatorClient init [host=%s, port=%s]', host, port)

    def serial(self) -> str:
        data = self._read_element(ObjectIdEnum.serial)
        serial = data.serial.strip()
        logger.info('serial [%s]', serial)
        return serial

    def clock_time(self) -> datetime:
        data = self._read_element(ObjectIdEnum.time)
        date_obj = datetime.datetime(
            2000 + data.year, data.month, data.date, data.hour, data.minute, data.second)
        logger.info('time [%s]', date_obj.isoformat())
        return date_obj

    def csq(self) -> int:
        data = self._read_element(ObjectIdEnum.csq_net_op)
        logger.info('csq [%s]', data.csq)
        return data.csq

    def prepay_enabled(self) -> bool:
        data = self._read_element(ObjectIdEnum.prepay_enabled_flag)
        enabled: bool = data.enabled_flag == 1
        logger.info('prepay enabled [%s]', enabled)
        return enabled

    def prepay_balance(self) -> float:
        data = self._read_element(ObjectIdEnum.prepay_balance)
        logger.debug('prepay balance raw [%s]', data.balance)
        balance_gbp: float = data.balance / 100000
        logger.info('prepay balance to GBP [%s]', balance_gbp)
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
