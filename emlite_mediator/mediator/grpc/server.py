import grpc
import os
import signal
import sys
import time

from concurrent import futures
from datetime import datetime, timedelta

from emlite_mediator.emlite.emlite_api import EmliteAPI
from emlite_mediator.util.logging import get_logger

from .generated.mediator_pb2 import ReadElementReply, SendRawMessageReply
from .generated.mediator_pb2_grpc import EmliteMediatorServiceServicer, add_EmliteMediatorServiceServicer_to_server

logger = get_logger(__name__, __file__)

"""
    Wait this amount of time between requests to avoid the emlite meter
    returning "connection refused" errors. 
"""
minimum_time_between_emlite_requests_seconds = 4

"""
    Allow one request to the meter at a time only. 
"""
max_workers = 1

"""
    Address details of the Emlite meter. 
"""
emlite_host = os.environ.get('EMLITE_HOST')
emlite_port = os.environ.get('EMLITE_PORT') or '8080'

"""
    Port to listen on. 
"""
listen_port = os.environ.get('LISTEN_PORT') or '50051'

"""
    The mediator is a gRPC server that takes requests and relays them to an
    Emlite meter over the EMOP protocol.

    Clients can send a raw data_field or request just a specific object_id request
    and the mediator will build a corresponding Emlite frame to send to the meter.

    Only one emlite meter request can be processed at a time so this server
    will queue incoming gRPC requests and process them one at a time.
    This is achieved by simply setting max_workers=1 on the grpc server.
     
    Additionally there will be a wait of minimum_time_between_emlite_requests_seconds
    between back to back requests. Therefore client requests will have to wait
    a little if a number of requests are in the queue.

    NOTE: this performance could potentially be improved by reusing the socket
    connection however at this stage a higher throughput is not required.
"""


class EmliteMediatorServicer(EmliteMediatorServiceServicer):
    def __init__(self, host, port):
        self.api = EmliteAPI(host, port)

    def sendRawMessage(self, request, context):
        logger.info('sendRawMessage', message=request.dataField.hex())
        self._space_out_requests()
        try:
            rsp_payload = self.api.send_message(request.dataField)
            logger.info('sendRawMessage response', payload=rsp_payload.hex())
            return SendRawMessageReply(response=rsp_payload)
        except Exception as e:
            self._handle_failure(e, 'sendRawMessage', context)
            return SendRawMessageReply()

    def readElement(self, request, context):
        object_id_bytes = request.objectId.to_bytes(3, byteorder='big')
        logger.info('readElement request', object_id=object_id_bytes.hex())
        self._space_out_requests()
        try:
            rsp_payload = self.api.read_element_with_object_id_bytes(
                object_id_bytes)
            logger.info('readElement response', payload=rsp_payload.hex())
            return ReadElementReply(response=rsp_payload)
        except Exception as e:
            self._handle_failure(e, 'readElement', context)
            return ReadElementReply()

    def _handle_failure(self, exception, call_name, context):
        logger.exception('call failed', call_name=call_name)
        context.set_code(grpc.StatusCode.INTERNAL)
        context.set_details("network failure or internal error")

    """ sleep the minimum amount of time between requests if there was a request recently in that range """

    def _space_out_requests(self):
        if (self.api.last_request_datetime == None):
            return

        next_request_allowed_datetime = self.api.last_request_datetime + \
            timedelta(seconds=minimum_time_between_emlite_requests_seconds)

        if (datetime.now() < next_request_allowed_datetime):
            logger.info('sleeping %s seconds between requests',
                        minimum_time_between_emlite_requests_seconds)
            time.sleep(minimum_time_between_emlite_requests_seconds)


def shutdown_handler(signal, frame):
    print("\nServer shutting down...")
    sys.exit(0)


def serve():
    global logger
    logger = logger.bind(emlite_host=emlite_host, listen_port=listen_port)

    if (emlite_host is None):
        logger.error('EMLITE_HOST environment variable not set')
        return

    logger.info("starting server")

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    add_EmliteMediatorServiceServicer_to_server(
        EmliteMediatorServicer(emlite_host, emlite_port), server)

    server.add_insecure_port(f'[::]:{listen_port}')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, shutdown_handler)
    serve()
