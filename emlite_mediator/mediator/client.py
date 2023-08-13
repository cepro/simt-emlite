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

from .grpc.client import vars

FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger(__name__)

emliteHost = os.environ.get('EMLITE_HOST')
emlitePort = os.environ.get('EMLITE_PORT') or 8080

class EmliteMediatorClient():
    def __init__(self, grpc_client):
        logger.info('init')
        
    def serial(self):
        logger.info('serial')


        # if (object_id == ObjectIdEnum.serial):
        #     logger.info('serial %s', data.serial.strip())   
        # elif (object_id == ObjectIdEnum.time):
        #     date_obj = datetime.datetime(2000 + data.year, data.month, data.date, data.hour, data.minute, data.second)
        #     logger.info('time %s', date_obj.isoformat())   
        # elif (object_id == ObjectIdEnum.csq_net_op):
        #     logger.info('csq %s', data.csq)   
        # else:
        #     logger.info('response %s', payload_bytes.response.hex(