import base64
import os
import signal
import sys
import threading
import time
from concurrent import futures
from datetime import datetime, timedelta

from emop_frame_protocol.util import emop_encode_u3be

import grpc
from simt_emlite.emlite.emlite_api import EmliteAPI
from simt_emlite.util.logging import get_logger

from .generated.mediator_pb2 import (
    ReadElementReply,
    SendRawMessageReply,
    WriteElementReply,
)
from .generated.mediator_pb2_grpc import (
    EmliteMediatorServiceServicer,
    add_EmliteMediatorServiceServicer_to_server,
)

logger = get_logger(__name__, __file__)

"""
    Wait this amount of time between requests to avoid the emlite meter
    returning "connection refused" errors. 
"""
minimum_time_between_emlite_requests_seconds = 2

"""
    Allow one request to the meter at a time only. 
"""
max_workers = 1

"""
    Address details of the Emlite meter. 
"""
emlite_host = os.environ.get("EMLITE_HOST")
emlite_port = os.environ.get("EMLITE_PORT") or "8080"

"""
    Port to listen on. 
"""
listen_port = os.environ.get("LISTEN_PORT") or "50051"

"""
    Auth Certificates and Keys. 
"""
server_cert_b64 = os.environ.get("MEDIATOR_SERVER_CERT")
server_key_b64 = os.environ.get("MEDIATOR_SERVER_KEY")
ca_cert_b64 = os.environ.get("MEDIATOR_CA_CERT")

use_cert_auth = (
    server_cert_b64 is not None
    and server_key_b64 is not None
    and ca_cert_b64 is not None
)

"""
    Inactive shutdown properties 
"""

inactivity_seconds = int(os.environ.get("MEDIATOR_INACTIVITY_SECONDS") or "0")
inactivity_check_interval_seconds = 30


def epoch_seconds():
    return round(time.time())


last_request_time = epoch_seconds()
inactivity_event = threading.Event()

server = None

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
        self.log = logger.bind(emlite_host=host)

    def sendRawMessage(self, request, context):
        self._refresh_last_request_time()
        self.log.info("sendRawMessage", message=request.dataField.hex())
        self._space_out_requests()
        try:
            rsp_payload = self.api.send_message(request.dataField)
            self.log.info("sendRawMessage response", payload=rsp_payload.hex())
            return SendRawMessageReply(response=rsp_payload)
        except Exception as e:
            self._handle_failure(e, "sendRawMessage", context)
            return SendRawMessageReply()

    def readElement(self, request, context):
        self._refresh_last_request_time()
        object_id_bytes = emop_encode_u3be(request.objectId)
        self.log.info("readElement request", object_id=object_id_bytes.hex())
        self._space_out_requests()
        try:
            rsp_payload = self.api.read_element(object_id_bytes)
            self.log.info(
                "readElement response",
                object_id=object_id_bytes.hex(),
                payload=rsp_payload.hex(),
            )
            return ReadElementReply(response=rsp_payload)
        except Exception as e:
            self._handle_failure(e, "readElement", context)
            return ReadElementReply()

    def writeElement(self, request, context):
        self._refresh_last_request_time()
        object_id_bytes = emop_encode_u3be(request.objectId)
        self.log.info(
            "writeElement request",
            object_id=object_id_bytes.hex(),
            payload=request.payload.hex(),
        )
        self._space_out_requests()
        try:
            self.api.write_element(object_id_bytes, request.payload)
            self.log.info(
                "writeElement returned",
                object_id=object_id_bytes.hex(),
            )
            return WriteElementReply()
        except Exception as e:
            self._handle_failure(e, "writeElement", context)
            return WriteElementReply()

    def _handle_failure(self, exception: Exception, call_name: str, context):
        if exception.__class__.__name__.startswith("RetryError"):
            self.log.warn(
                "Failed to connect to meter after a number of retries",
                call_name=call_name,
            )
            context.set_details("failed to connect after retries")
        elif exception.__class__.__name__.startswith("EOFError"):
            self.log.warn(
                "EOFError seen - so far only happens on back to back calls for 3p voltage",
                call_name=call_name,
            )
            context.set_details("EOFError")
        else:
            self.log.error(
                "call failed", call_name=call_name, error=exception, exception=exception
            )
            context.set_details("network failure or internal error")

        context.set_code(grpc.StatusCode.INTERNAL)

    """ sleep the minimum amount of time between requests if there was a request recently in that range """

    def _space_out_requests(self):
        if self.api.last_request_datetime is None:
            return

        next_request_allowed_datetime = self.api.last_request_datetime + timedelta(
            seconds=minimum_time_between_emlite_requests_seconds
        )

        if datetime.now() < next_request_allowed_datetime:
            self.log.info(
                "sleeping %s seconds between requests",
                minimum_time_between_emlite_requests_seconds,
            )
            time.sleep(minimum_time_between_emlite_requests_seconds)

    def _refresh_last_request_time(self):
        global last_request_time
        last_request_time = epoch_seconds()


def shutdown_handler(signal, frame):
    logger.info("Server shutting down...")
    sys.exit(0)


def inactivity_checking():
    """
    check for inactivity on a Timer and reaise event and exit the thread when reached
    """
    seconds_inactive = epoch_seconds() - last_request_time
    if seconds_inactive >= inactivity_seconds:
        logger.info(f"Server inactive for {seconds_inactive} seconds")
        global inactivity_event
        inactivity_event.set()
        sys.exit(0)
    else:
        threading.Timer(inactivity_check_interval_seconds, inactivity_checking).start()


def decode_b64_secret_to_bytes(b64_secret: str) -> bytes:
    return (
        base64.b64decode(b64_secret)
        .decode("utf-8")
        .replace("\\n", "\n")
        .encode("utf-8")
    )


def serve():
    global logger
    log = logger.bind(emlite_host=emlite_host)

    if emlite_host is None:
        log.error("EMLITE_HOST environment variable not set")
        return

    log.info("starting server")

    global server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    add_EmliteMediatorServiceServicer_to_server(
        EmliteMediatorServicer(emlite_host, emlite_port), server
    )

    listen_address = f"0.0.0.0:{listen_port}"

    if use_cert_auth:
        server_cert = decode_b64_secret_to_bytes(server_cert_b64)
        server_key = decode_b64_secret_to_bytes(server_key_b64)
        ca_cert = decode_b64_secret_to_bytes(ca_cert_b64)

        server_credentials = grpc.ssl_server_credentials(
            [(server_key, server_cert)],
            root_certificates=ca_cert,
            require_client_auth=True,
        )

        log.info(f"add_secure_port [{listen_address}]")
        server.add_secure_port(listen_address, server_credentials)

        # add a private as well for internal services like meter sync jobs
        private_listen_address = "0.0.0.0:44444"
        log.info(f"add_insecure_port [{private_listen_address}]")
        server.add_insecure_port(private_listen_address)
    else:
        log.info(f"add_insecure_port [{listen_address}]")
        server.add_insecure_port(listen_address)

    server.start()

    if inactivity_seconds > 0:
        inactivity_checking()
        inactivity_event.wait()
        shutdown_handler(None, None)
    else:
        server.wait_for_termination()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    serve()
