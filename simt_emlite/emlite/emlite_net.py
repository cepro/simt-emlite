import os
import socket

from python_socks import (  # type: ignore[import-untyped]
    ProxyConnectionError,
    ProxyError,
    ProxyTimeoutError,
)
from python_socks.sync import Proxy  # type: ignore[import-untyped]
from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
)

from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)

socket_timeout_seconds: float = float(os.environ.get("EMLITE_TIMEOUT_SECONDS") or 20.0)


socks_host: str | None = os.environ.get("SOCKS_HOST")
socks_port: str | None = os.environ.get("SOCKS_PORT")
socks_username: str | None = os.environ.get("SOCKS_USERNAME")
socks_password: str | None = os.environ.get("SOCKS_PASSWORD")

use_socks = all(
    v is not None for v in [socks_host, socks_port, socks_username, socks_password]
)

num_retries_send_message = 5

"""
    Class responsible for talking to meters via TCP/IP.

    This class has no knowledge of the structure of the bytes it's sending
    and receiving. Just manages raw communication of bytes.
"""


class EmliteNET:
    def __init__(self, host: str, port: int = 8080) -> None:
        self.host = host
        self.port = int(port)
        global logger
        logger = logger.bind(host=host)

    @retry(stop=stop_after_attempt(num_retries_send_message), wait=wait_fixed(7))
    def send_message(self, req_bytes: bytes) -> bytes:
        sock = self._open_socket(self.send_message.statistics["attempt_number"])  # type: ignore[attr-defined]
        try:
            logger.debug("sending", request_payload=req_bytes.hex())
            self._write_bytes(sock, req_bytes)
            rsp_bytes = self._read_bytes(sock, 512)
            sock.close()
        except socket.timeout as e:
            logger.warn("Timeout in send_message")
            sock.close()
            raise e
        except socket.error as e:
            logger.error(f"socket.error {e}")
            sock.close()
            raise e
        logger.info("received response", response_payload=rsp_bytes.hex())
        return rsp_bytes

    def _open_socket(self, attempt: int | None = None) -> socket.socket:
        try:
            if use_socks is True:
                logger.debug(
                    "use socks",
                )
                proxy = Proxy.from_url(
                    f"socks5://{socks_username}:{socks_password}@{socks_host}:{socks_port}"
                )
                logger.debug(
                    "proxy.connect()",
                    socks_host=socks_host,
                    socks_port=socks_port,
                    socks_username=socks_username,
                    attempt=attempt,
                )
                sock: socket.socket = proxy.connect(
                    dest_host=self.host, dest_port=self.port, timeout=10
                )
                logger.debug("connected")
            else:
                sock = socket.socket()
                logger.debug("connect()")
                sock.connect((self.host, self.port))

            sock.settimeout(socket_timeout_seconds)

        except ProxyTimeoutError as e:
            # very common so log at debug level
            logger.debug("timeout connecting to meter by proxy")
            sock.close()
            # raise again will be caught by @retry
            raise e
        except ProxyError as e:
            err_str = str(e)
            if err_str == "Connection refused by destination host":
                # very common so log at debug level
                logger.debug(err_str)
            else:
                attempt_num = self.send_message.statistics["attempt_number"]  # type: ignore[attr-defined]
                log_level = (
                    "error" if attempt_num == num_retries_send_message else "warn"
                )
                getattr(logger, log_level)(
                    f"ProxyError: {err_str}", attempt=attempt_num
                )
            sock.close()
            # raise again will be caught by @retry
            raise e
        except ProxyConnectionError as e:
            # log as info as this occurs often and is usually handled via the @retry further up the stack
            #
            # generally this occurs because the emnify-gateway is being restarted which is unfortunately
            # a number of times a day
            logger.info(f"socks proxy connection failure [{e}]")
            sock.close()
            # raise again will be caught by @retry
            raise e
        except socket.timeout as e:
            logger.info("timeout connecting to socket", error=e)
            sock.close()
            # raise again will be caught by @retry
            raise e
        except socket.error as e:
            if e.__class__.__name__ == "ConnectionRefusedError":
                # The meter is likely not ready to accept the second of 2 requests
                # we can observe a lot of these if there is no wait time between
                # requests. we currently wait 2 seconds between them which avoids
                # a lot of these but sometimes they still occur.
                #
                # NOTE: Care is taken here not to log the string 'error' so it
                # doesn't appear in papertrail filters for errors. We tolerate these
                # and often a retry succeeds.
                logger.warn("ConnectionRefused connecting to socket")
            else:
                logger.warn("Error connecting to socket", error=e)
            sock.close()
            # raise again will be caught by @retry
            raise e
        except Exception as e:
            logger.error(
                f"catch all exception in _open_socket: [class={e.__class__.__name__}] [{e}] "
            )
            raise e

        return sock

    def _write_bytes(self, sock: socket.socket, data: bytes) -> None:
        try:
            sock.send(data)
        except socket.error as e:
            logger.error("Error writing to socket", error=e)
            raise e

    def _read_bytes(self, sock: socket.socket, num_bytes: int) -> bytes:
        try:
            return sock.recv(num_bytes)
        except socket.error as e:
            logger.warn("Error reading from socket", error=e)
            raise e
