import logging
import grpc

from .generated.emlite_mediator_pb2 import SendMessageRequest
from .generated.emlite_mediator_pb2_grpc import EmliteMediatorServiceStub

def send_message(stub, message):
    rsp = stub.sendMessage(SendMessageRequest(dataFrame=message))
    print(rsp.response.hex())   

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = EmliteMediatorServiceStub(channel)
        message = bytes.fromhex('7E110000000080D1C2480001600100001C32')
        send_message(stub, message)

if __name__ == '__main__':
    logging.basicConfig()
    run()