# Copyright 2015 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The Python implementation of the gRPC route guide server."""

from concurrent import futures
from datetime import datetime, timedelta
import logging
import signal
import sys
import time
import grpc
import os

from emlite_mediator.emlite.emlite_api import EmliteAPI

from .generated.mediator_pb2 import ReadElementReply, SendRawMessageReply
from .generated.mediator_pb2_grpc import EmliteMediatorServiceServicer, add_EmliteMediatorServiceServicer_to_server

FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
emliteHost = os.environ.get('EMLITE_HOST')
emlitePort = os.environ.get('EMLITE_PORT') or '8080'

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
        logger.info('__init__ host [%s] port [%s]', host, port)
        self.api = EmliteAPI(host, port)

    def sendRawMessage(self, request, context):
        logger.info('sendRawMessage: received=[%s]', request.dataField.hex())
        self._space_out_requests()
        try:
            rsp_payload = self.api.send_message(request.dataField)
            logger.info('sendRawMessage: response=[%s]', rsp_payload.hex())
            return SendRawMessageReply(response=rsp_payload)
        except Exception as e:
            self._handle_failure(e, 'sendRawMessage', context)
            return SendRawMessageReply()

    def readElement(self, request, context):
        object_id_bytes = request.objectId.to_bytes(3, byteorder='big')
        logger.info('readElement: object_id=[0x%s]', object_id_bytes.hex())
        self._space_out_requests()
        try:
            rsp_payload = self.api.read_element_with_object_id_bytes(
                object_id_bytes)
            logger.info('readElement: response=[%s]', rsp_payload.hex())
            return ReadElementReply(response=rsp_payload)
        except Exception as e:
            self._handle_failure(e, 'readElement', context)
            return ReadElementReply()

    def _handle_failure(self, exception, call_name, context):
        logger.exception('%s failed: %s', call_name, exception)
        context.set_code(grpc.StatusCode.INTERNAL)
        context.set_details("network failure or internal error")

    """ sleep the minimum amount of time between requests if there was a request recently in that range """

    def _space_out_requests(self):
        if (self.api.last_request_datetime == None):
            return

        next_request_allowed_datetime = self.api.last_request_datetime + \
            timedelta(seconds=minimum_time_between_emlite_requests_seconds)

        if (datetime.now() < next_request_allowed_datetime):
            logger.info('sleeping between close requests')
            time.sleep(minimum_time_between_emlite_requests_seconds)


def shutdown_handler(signal, frame):
    print("\nServer shutting down...")
    sys.exit(0)


def serve():
    if (emliteHost is None):
        logger.error('EMLITE_HOST environment variable not set')
        return

    port = 50051
    logger.info('starting server on %s', port)
    logger.info('meter: %s:%s', emliteHost, emlitePort)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    add_EmliteMediatorServiceServicer_to_server(
        EmliteMediatorServicer(emliteHost, emlitePort), server)

    server.add_insecure_port(f'[::]:{port}')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, shutdown_handler)
    serve()
