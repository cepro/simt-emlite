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

from .generated.emlite_mediator_pb2 import SendMessageReply
from .generated.emlite_mediator_pb2_grpc import EmliteMediatorServiceServicer, add_EmliteMediatorServiceServicer_to_server

FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

class EmliteMediatorServicer(EmliteMediatorServiceServicer):
    """Provides methods that implement functionality of emlite mediator server."""

    def sendMessage(self, request, context):
        logger.info('sendMessage: received=[%s]', request.dataFrame.hex())
        return SendMessageReply(response=bytes.fromhex('deadbeef'))

def serve():
    port = 50051
    logger.info('starting server on %s', port)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    add_EmliteMediatorServiceServicer_to_server(
        EmliteMediatorServicer(), server)
    
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()