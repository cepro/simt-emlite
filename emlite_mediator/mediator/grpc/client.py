from emlite_mediator.util.logging import get_logger

import grpc

from kaitaistruct import KaitaiStream, BytesIO

from emlite_mediator.emlite.messages.emlite_response import EmliteResponse
from emlite_mediator.emlite.messages.emlite_object_id_enum import ObjectIdEnum

from .generated.mediator_pb2 import ReadElementRequest, SendRawMessageRequest
from .generated.mediator_pb2_grpc import EmliteMediatorServiceStub

logger = get_logger(__name__, __file__)

TIMEOUT_SECONDS = 15


class EmliteMediatorGrpcClient():
    def __init__(self, host='0.0.0.0', port=50051):
        self.address = f"{host}:{port}"
        global logger
        logger = logger.bind(host=host, port=port)

    def read_element(self, object_id: ObjectIdEnum):
        with grpc.insecure_channel(self.address) as channel:
            stub = EmliteMediatorServiceStub(channel)
            try:
                rsp_obj = stub.readElement(
                    ReadElementRequest(objectId=object_id.value),
                    timeout=TIMEOUT_SECONDS)
            except grpc.RpcError as e:
                logger.error('readElement failed',
                             details=e.details(), code=e.code(), object_id=object_id.name)
                raise e

        payload_bytes = rsp_obj.response
        logger.info('response received', response_payload=payload_bytes.hex())

        emlite_rsp = EmliteResponse(
            len(payload_bytes), object_id, KaitaiStream(BytesIO(payload_bytes)))
        emlite_rsp._read()
        return emlite_rsp.response

    def send_message(self, message: bytes):
        with grpc.insecure_channel(self.address) as channel:
            stub = EmliteMediatorServiceStub(channel)
            try:
                rsp_obj = stub.sendRawMessage(
                    SendRawMessageRequest(dataField=message),
                    timeout=TIMEOUT_SECONDS)
            except grpc.RpcError as e:
                logger.error('sendRawMessage',
                             details=e.details(), code=e.code())
                raise e

        payload_bytes = rsp_obj.response
        logger.info('response received', response_payload=payload_bytes.hex())
        return payload_bytes


if __name__ == '__main__':
    client = EmliteMediatorGrpcClient()
    client.read_element(ObjectIdEnum.serial)
    # client.send_message(bytes.fromhex('0160010000'))
