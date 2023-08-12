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
import logging
import grpc
import os

from emlite_mediator.emlite.emlite_api import EmliteAPI

from .generated.emlite_mediator_pb2 import ReadElementReply, SendRawMessageReply
from .generated.emlite_mediator_pb2_grpc import EmliteMediatorServiceServicer, add_EmliteMediatorServiceServicer_to_server

FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger(__name__)

emliteHost = os.environ.get('EMLITE_HOST')
emlitePort = os.environ.get('EMLITE_PORT')

class EmliteMediatorServicer(EmliteMediatorServiceServicer):
    def __init__(self, host, port):
        self.api = EmliteAPI(host, port)

    def sendRawMessage(self, request, context):
        logger.info('sendRawMessage: received=[%s]', request.dataField.hex())
        try:
            rsp_payload = self.api.send_message(request.dataField)
            logger.info('sendRawMessage: response=[%s]', rsp_payload.hex())
            return SendRawMessageReply(response=rsp_payload)
        except Exception as e:
            logger.exception('sendRawMessage failed %s', e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("network failure or internal error")
            return SendRawMessageReply()

    def readElement(self, request, context):
        object_id_bytes = request.objectId.to_bytes(3, byteorder='big')
        logger.info('readElement: object_id=[0x%s]', object_id_bytes.hex())
        try:
            rsp_payload = self.api.read_element_with_object_id_bytes(object_id_bytes)
            logger.info('readElement: response=[%s]', rsp_payload.hex())
            return ReadElementReply(response=rsp_payload)
        except Exception as e:
            logger.exception('readElement failed %s', e)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("network failure or internal error")
            return ReadElementReply()

def serve():
    if (emliteHost is None or emlitePort is None):
        logger.error('EMLITE_HOST and EMLITE_PORT environment variables not set')
        return

    port = 50051
    logger.info('starting server on %s', port)
    logger.info('meter: %s:%s', emliteHost, emlitePort)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    add_EmliteMediatorServiceServicer_to_server(
        EmliteMediatorServicer(emliteHost, emlitePort), server)
    
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()