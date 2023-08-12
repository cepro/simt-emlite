import datetime
import logging
import grpc
import sys

from kaitaistruct import KaitaiStream, BytesIO

from emlite_mediator.emlite.messages.emlite_response import EmliteResponse
from emlite_mediator.emlite.messages.emlite_object_id_enum import ObjectIdEnum

from .generated.emlite_mediator_pb2 import ObjectId, ReadElementRequest, SendRawMessageRequest
from .generated.emlite_mediator_pb2_grpc import EmliteMediatorServiceStub

FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger(__name__)

def send_message(stub, message):
    try:
        rsp = stub.sendRawMessage(SendRawMessageRequest(dataField=message))
    except grpc.RpcError as e:
        logger.error('sendRawMessage failed: [%s] (code: %s)', e.details(), e.code())
    return rsp

def read_element(stub, object_id):
    try:
        return stub.readElement(ReadElementRequest(objectId=object_id))
    except grpc.RpcError as e:
        logger.error('readElement failed: [%s] (code: %s)', e.details(), e.code())
        raise e
    
def run(mediator_address):
    with grpc.insecure_channel(mediator_address) as channel:
        stub = EmliteMediatorServiceStub(channel)

        # get serial by raw message:
        # rsp = send_message(stub, bytes.fromhex('0160010000'))

        # object_id_grpc = ObjectId.TIME
        object_id_grpc = ObjectId.CSQ_NET_OP
        payload_bytes = read_element(stub, object_id_grpc).response
        logger.info('payload_bytes: [%s]', payload_bytes.hex())

        object_id = ObjectIdEnum.csq_net_op
        emlite_rsp = EmliteResponse(len(payload_bytes), object_id, KaitaiStream(BytesIO(payload_bytes)))
        emlite_rsp._read()

        data = emlite_rsp.response
        if (object_id == ObjectIdEnum.serial):
            logger.info('serial %s', data.serial.strip())   
        elif (object_id == ObjectIdEnum.time):
            date_obj = datetime.datetime(2000 + data.year, data.month, data.date, data.hour, data.minute, data.second)
            logger.info('time %s', date_obj.isoformat())   
        elif (object_id == ObjectIdEnum.csq_net_op):
            logger.info('csq %s', data.csq)   
        else:
            logger.info('response %s', payload_bytes.response.hex())   

if __name__ == '__main__':
    mediator_port = 50051
    if (len(sys.argv) > 1):
        mediator_port = sys.argv[1]
    mediator_address = f"localhost:{mediator_port}"
    run(mediator_address)