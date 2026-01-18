import os
import signal
import sys
from concurrent import futures

import grpc
from simt_emlite.util.logging import get_logger

from .generated.mediator_pb2_grpc import (
    add_EmliteMediatorServiceServicer_to_server,
    add_InfoServiceServicer_to_server,
)
from .info_service import EmliteInfoServiceServicer
from .mediator_service import EmliteMediatorServicerV2
from .meter_registry import MeterRegistry
from .util import decode_b64_secret_to_bytes

logger = get_logger(__name__, __file__)

LISTEN_PORT = os.environ.get("LISTEN_PORT", "50051")
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "30"))

# Auth Certificates and Keys
server_cert_b64 = os.environ.get("MEDIATOR_SERVER_CERT")
server_key_b64 = os.environ.get("MEDIATOR_SERVER_KEY")
ca_cert_b64 = os.environ.get("MEDIATOR_CA_CERT")

esco_code = os.environ.get("ESCO")

use_cert_auth = (
    server_cert_b64 is not None
    and server_key_b64 is not None
    and ca_cert_b64 is not None
)


def shutdown_handler(signal_num, frame):
    logger.info("Server shutting down...")
    sys.exit(0)


def serve():
    registry = MeterRegistry(esco_code=esco_code)
    registry.refresh_from_db()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=MAX_WORKERS))

    # Register Services
    add_EmliteMediatorServiceServicer_to_server(
        EmliteMediatorServicerV2(registry), server
    )
    add_InfoServiceServicer_to_server(EmliteInfoServiceServicer(), server)

    listen_address = f"0.0.0.0:{LISTEN_PORT}"

    if use_cert_auth:
        try:
            server_cert = decode_b64_secret_to_bytes(server_cert_b64)
            server_key = decode_b64_secret_to_bytes(server_key_b64)
            ca_cert = decode_b64_secret_to_bytes(ca_cert_b64)

            server_credentials = grpc.ssl_server_credentials(
                [(server_key, server_cert)],
                root_certificates=ca_cert,
                require_client_auth=True,
            )

            logger.debug(f"add_secure_port [{listen_address}]")
            server.add_secure_port(listen_address, server_credentials)

            # add a private as well for internal services like meter sync jobs
            private_listen_address = "0.0.0.0:44444"
            logger.debug(f"add_insecure_port [{private_listen_address}]")
            server.add_insecure_port(private_listen_address)
        except Exception as e:
            logger.error(f"Failed to setup SSL credentials: {e}")
            sys.exit(1)
    else:
        logger.debug(f"add_insecure_port [{listen_address}]")
        server.add_insecure_port(listen_address)

    logger.info(f"Server V2 starting with {MAX_WORKERS} workers")

    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    import argparse
    import logging

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    signal.signal(signal.SIGINT, shutdown_handler)
    serve()
