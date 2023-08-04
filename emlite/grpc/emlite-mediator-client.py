import logging
import grpc

from .generated.emlite_mediator_pb2 import SendMessageRequest
from .generated.emlite_mediator_pb2_grpc import EmliteMediatorServiceStub

FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

def send_message(stub, message):
    try:
        rsp = stub.sendMessage(SendMessageRequest(dataFrame=message))
        logger.info('got serial %s', rsp.response.decode('ascii'))   
    except grpc.RpcError as e:
        logger.error('send message failed: [%s] (code: %s)', e.details(), e.code())

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = EmliteMediatorServiceStub(channel)
        message = bytes.fromhex('7E110000000080D1C2480001600100001C32')
        send_message(stub, message)

if __name__ == '__main__':
    logging.basicConfig()
    run()