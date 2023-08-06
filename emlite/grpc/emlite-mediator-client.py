import logging
import grpc
import sys

from .generated.emlite_mediator_pb2 import ObjectId, ReadElementRequest, SendRawMessageRequest
from .generated.emlite_mediator_pb2_grpc import EmliteMediatorServiceStub

FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

def send_message(stub, message):
    try:
        rsp = stub.sendRawMessage(SendRawMessageRequest(dataField=message))
        logger.info('got serial %s', rsp.response.decode('ascii'))   
    except grpc.RpcError as e:
        logger.error('sendRawMessage failed: [%s] (code: %s)', e.details(), e.code())

def read_element(stub, object_id):
    try:
        rsp = stub.readElement(ReadElementRequest(objectId=object_id))
    except grpc.RpcError as e:
        logger.error('readElement failed: [%s] (code: %s)', e.details(), e.code())

    if (object_id == ObjectId.SERIAL):
        logger.info('got serial %s', rsp.response.decode('ascii'))   
    else:
        logger.info('got response %s', rsp.response.hex())   

def run(mediator_address):
    with grpc.insecure_channel(mediator_address) as channel:
        stub = EmliteMediatorServiceStub(channel)

        message = bytes.fromhex('0160010000')
        send_message(stub, message)

        # read_element(stub, ObjectId.SERIAL)

if __name__ == '__main__':
    if (len(sys.argv) == 1):
        print('Usage: emlite-mediator-client <port of mediator on host>')
        exit()
    
    logging.basicConfig()
    mediator_port = sys.argv[1]
    mediator_address = f"localhost:{mediator_port}"
    run(mediator_address)