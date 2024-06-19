import os

from emop_frame_protocol.emop_message import EmopMessage
from emop_frame_protocol.emop_object_id_enum import ObjectIdEnum
from emop_frame_protocol.vendor.kaitaistruct import BytesIO, KaitaiStream

import grpc
from simt_emlite.mediator.grpc.exception.EmliteConnectionFailure import (
    EmliteConnectionFailure,
)
from simt_emlite.mediator.grpc.exception.EmliteEOFError import EmliteEOFError
from simt_emlite.util.logging import get_logger

from .generated.mediator_pb2 import (
    ReadElementRequest,
    SendRawMessageRequest,
    WriteElementRequest,
)
from .generated.mediator_pb2_grpc import EmliteMediatorServiceStub

logger = get_logger(__name__, __file__)

PROXY_HOST = os.environ.get("MEDIATOR_PROXY_HOST")
PROXY_CERT_PATH = os.environ.get("MEDIATOR_PROXY_CERTIFICATE_PATH")

PROXY_CERT = None
if PROXY_CERT_PATH is not None:
    with open(PROXY_CERT_PATH, "rb") as cert_file:
        PROXY_CERT = cert_file.read()


# timeout considerations:
# 1) a successful call should take less than 5 seconds
# 2) emlite_net retries 3 times in case of timeouts, timeout is 10 seconds with
# a 1 second pause between each retry
# 3) grpc server queues requests and pauses for 4 seconds between each
TIMEOUT_SECONDS = 50


class EmliteMediatorGrpcClient:
    def __init__(
        self,
        mediator_host="0.0.0.0",
        access_token=None,
        meter_id=None,
        proxy_host_override=None,
        proxy_cert_override=None,
    ):
        self.mediator_host = mediator_host
        self.access_token = access_token
        self.meter_id = meter_id if meter_id is not None else "unknown"

        self.proxy_host = (
            proxy_host_override if proxy_host_override is not None else PROXY_HOST
        )
        self.proxy_cert = (
            proxy_cert_override if proxy_cert_override is not None else PROXY_CERT
        )

        self.proxy_address = f"{self.proxy_host}:1443"

        global logger
        self.log = logger.bind(mediator_host=mediator_host, meter_id=meter_id)

    def read_element(self, object_id: ObjectIdEnum):
        with grpc.secure_channel(
            self.proxy_address, self._channel_credentials()
        ) as channel:
            stub = EmliteMediatorServiceStub(channel)
            try:
                rsp_obj = stub.readElement(
                    ReadElementRequest(objectId=object_id.value),
                    timeout=TIMEOUT_SECONDS,
                    metadata=self._call_metadata(),
                )
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                    self.log.warn(
                        "rpc timeout (deadline_exceeded)", object_id=object_id.name
                    )
                elif e.code() == grpc.StatusCode.INTERNAL:
                    if "EOFError" in e.details():
                        # TODO: need to fix these or retry - for now longer sleep between requests may resolve and we'll mark warn
                        self.log.warn(
                            "EOFError from meter - logging warn - so far only seen with back to back 3p voltage requests",
                            object_id=object_id.name,
                        )
                        raise EmliteEOFError(
                            f"object_id={object_id.name}, meter={self.meter_id}"
                        )
                    elif "failed to connect after retries" in e.details():
                        self.log.warn(e.details())
                        raise EmliteConnectionFailure(
                            f"object_id={object_id.name}, meter={self.meter_id}"
                        )
                    else:
                        raise e
                else:
                    self.log.error(
                        "readElement failed",
                        details=e.details(),
                        code=e.code(),
                        object_id=object_id.name,
                    )
                raise e

        payload_bytes = rsp_obj.response
        self.log.info("response received", response_payload=payload_bytes.hex())

        emlite_rsp = EmopMessage(
            len(payload_bytes), object_id, KaitaiStream(BytesIO(payload_bytes))
        )
        emlite_rsp._read()
        return emlite_rsp.message

    def write_element(self, object_id: ObjectIdEnum, payload: bytes):
        with grpc.secure_channel(
            self.proxy_address, self._channel_credentials()
        ) as channel:
            stub = EmliteMediatorServiceStub(channel)
            try:
                stub.writeElement(
                    WriteElementRequest(objectId=object_id.value, payload=payload),
                    timeout=TIMEOUT_SECONDS,
                    metadata=self._call_metadata(),
                )
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                    self.log.warn(
                        "rpc timeout (deadline_exceeded)", object_id=object_id.name
                    )
                elif e.code() == grpc.StatusCode.INTERNAL:
                    if "EOFError" in e.details():
                        # TODO: need to fix these or retry - for now longer sleep between requests may resolve and we'll mark warn
                        self.log.warn(
                            "EOFError from meter - logging warn - so far only seen with back to back 3p voltage requests",
                            object_id=object_id.name,
                        )
                        raise EmliteEOFError(
                            "object_id=" + object_id.name + ", meter=" + self.meter_id
                        )
                    elif "failed to connect after retries" in e.details():
                        self.log.warn(e.details())
                        raise EmliteConnectionFailure(
                            "object_id=" + object_id.name + ", meter=" + self.meter_id
                        )
                    else:
                        raise e
                else:
                    self.log.error(
                        "writeElement failed",
                        details=e.details(),
                        code=e.code(),
                        object_id=object_id.name,
                    )
                raise e

    def send_message(self, message: bytes):
        with grpc.secure_channel(
            self.proxy_address, self._channel_credentials()
        ) as channel:
            stub = EmliteMediatorServiceStub(channel)
            try:
                rsp_obj = stub.sendRawMessage(
                    SendRawMessageRequest(dataField=message),
                    timeout=TIMEOUT_SECONDS,
                    metadata=self._call_metadata(),
                )
            except grpc.RpcError as e:
                self.log.error("sendRawMessage", details=e.details(), code=e.code())
                raise e

        payload_bytes = rsp_obj.response
        self.log.info("response received", response_payload=payload_bytes.hex())
        return payload_bytes

    def _channel_credentials(self):
        channel_credential = grpc.ssl_channel_credentials(self.proxy_cert)
        call_credentials = grpc.access_token_call_credentials(self.access_token)
        composite_credentials = grpc.composite_channel_credentials(
            channel_credential,
            call_credentials,
        )
        return composite_credentials

    def _call_metadata(self):
        return (("http-mediator-host", self.mediator_host),)
