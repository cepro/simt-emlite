import logging
import grpc
import sys

from .generated.emlite_mediator_pb2 import SendRawMessageRequest
from .generated.emlite_mediator_pb2_grpc import EmliteMediatorServiceStub

FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

def send_message(stub, message):
    try:
        rsp = stub.sendRawMessage(SendRawMessageRequest(dataField=message))
        logger.info('got serial %s', rsp.response.decode('ascii'))   
    except grpc.RpcError as e:
        logger.error('send message failed: [%s] (code: %s)', e.details(), e.code())

def run(mediator_address):
    with grpc.insecure_channel(mediator_address) as channel:
        stub = EmliteMediatorServiceStub(channel)
        message = bytes.fromhex('0160010000')
        send_message(stub, message)

if __name__ == '__main__':
    if (len(sys.argv) == 1):
        print('Usage: emlite-mediator-client <port of mediator on host>')
        exit()
    
    logging.basicConfig()
    mediator_port = sys.argv[1]
    mediator_address = f"localhost:{mediator_port}"
    print(mediator_address)
    run(mediator_address)