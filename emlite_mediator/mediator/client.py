import datetime
import logging

from emlite_mediator.emlite.messages.emlite_object_id_enum import ObjectIdEnum
from .grpc.client import EmliteMediatorGrpcClient

FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger(__name__)

"""
    Use this class to make calls to an emlite meter through a mediator server.

    This is a wrapper around the gRPC client interface to the mediator server
    providing convencience functions to request each peice of data and get
    back a meaningful typed response.
"""


class EmliteMediatorClient():
    def __init__(self, host='0.0.0.0', port=50051):
        self.grpc_client = EmliteMediatorGrpcClient(host, port)
        logger.info('initialised')

    def serial(self) -> str:
        data = self.grpc_client.read_element(ObjectIdEnum.serial)
        serial = data.serial.strip()
        logger.info('serial [%s]', serial)
        return serial

    def clock_time(self) -> datetime:
        data = self.grpc_client.read_element(ObjectIdEnum.time)
        date_obj = datetime.datetime(
            2000 + data.year, data.month, data.date, data.hour, data.minute, data.second)
        logger.info('time [%s]', date_obj.isoformat())
        return date_obj

    def csq(self) -> int:
        data = self.grpc_client.read_element(ObjectIdEnum.csq_net_op)
        logger.info('csq [%s]', data.csq)
        return data.csq


if __name__ == '__main__':
    client = EmliteMediatorClient()
    print(client.clock_time())
    print(client.csq())
