

import grpc
from emop_frame_protocol.util import emop_encode_u3be  # type: ignore[import-untyped]

from .generated.mediator_pb2 import (
    ReadElementReply,
    SendRawMessageReply,
    WriteElementReply,
)
from .generated.mediator_pb2_grpc import EmliteMediatorServiceServicer
from .meter_registry import MeterRegistry, acquire_timeout, LOCK_TIMEOUT_SECONDS

from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)

class EmliteMediatorServicerV2(EmliteMediatorServiceServicer):
    def __init__(self, registry: MeterRegistry):
        self.registry = registry

    def _get_target_meter(self, context, request):
        """Helper to resolve meter from request field"""
        # Strategy A: Pass serial in the request body
        serial = getattr(request, 'serial', None)

        if not serial:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Target meter serial not specified")
            raise Exception("Target meter serial not specified")

        meter = self.registry.get_meter(serial)
        if not meter:
            context.abort(grpc.StatusCode.NOT_FOUND, f"Meter '{serial}' not known")

        return meter

    def readElement(self, request, context):
        try:
             meter = self._get_target_meter(context, request)
        except Exception:
             # _get_target_meter already calls context.abort
             return ReadElementReply()

        # Acquire per-meter lock
        try:
            with acquire_timeout(meter.lock, timeout=LOCK_TIMEOUT_SECONDS):
                meter.space_out_requests()

                object_id_bytes = emop_encode_u3be(request.objectId)
                logger.debug(f"readElement {request.objectId} for {meter.serial}")

                try:
                    rsp_payload = meter.api.read_element(object_id_bytes)
                    meter.mark_used()
                    return ReadElementReply(response=rsp_payload)
                except Exception as e:
                    logger.error(f"readElement failed for {meter.serial}: {e}")
                    context.abort(grpc.StatusCode.INTERNAL, "Meter communication failed")
                    return ReadElementReply()

        except TimeoutError:
             logger.warning(f"Timeout waiting for lock on meter {meter.serial}")
             context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED, f"Meter {meter.serial} is busy (timeout)")
             return ReadElementReply()

    def writeElement(self, request, context):
        try:
             meter = self._get_target_meter(context, request)
        except Exception:
             return WriteElementReply()

        try:
            with acquire_timeout(meter.lock, timeout=LOCK_TIMEOUT_SECONDS):
                meter.space_out_requests()

                object_id_bytes = emop_encode_u3be(request.objectId)
                logger.debug(f"writeElement {request.objectId} for {meter.serial}")

                try:
                    meter.api.write_element(object_id_bytes, request.payload)
                    meter.mark_used()
                    return WriteElementReply()
                except Exception as e:
                    logger.error(f"writeElement failed for {meter.serial}: {e}")
                    context.abort(grpc.StatusCode.INTERNAL, "Meter communication failed")
                    return WriteElementReply()

        except TimeoutError:
             context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED, f"Meter {meter.serial} is busy (timeout)")
             return WriteElementReply()

    def sendRawMessage(self, request, context):
        try:
             meter = self._get_target_meter(context, request)
        except Exception:
             return SendRawMessageReply()

        try:
            with acquire_timeout(meter.lock, timeout=LOCK_TIMEOUT_SECONDS):
                meter.space_out_requests()

                logger.debug(f"sendRawMessage for {meter.serial}")
                try:
                    rsp_payload = meter.api.send_message(request.dataField)
                    meter.mark_used()
                    return SendRawMessageReply(response=rsp_payload)
                except Exception as e:
                    logger.error(f"sendRawMessage failed for {meter.serial}: {e}")
                    context.abort(grpc.StatusCode.INTERNAL, "Meter communication failed")
                    return SendRawMessageReply()

        except TimeoutError:
             context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED, f"Meter {meter.serial} is busy (timeout)")
             return SendRawMessageReply()
