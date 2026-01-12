
import json

import traceback
import grpc
from simt_emlite.util.config import load_config
from simt_emlite.util.supabase import as_first_item, as_list, supa_client
from .generated.mediator_pb2 import GetInfoReply, GetMetersReply
from .generated.mediator_pb2_grpc import InfoServiceServicer

from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)

class EmliteInfoServiceServicer(InfoServiceServicer):
    def __init__(self):
        self.config = load_config()
        self.supabase_url = self.config["supabase_url"]
        self.supabase_anon_key = self.config["supabase_anon_key"]
        self.supabase_access_token = self.config["supabase_access_token"]

        if not self.supabase_url or not self.supabase_anon_key or not self.supabase_access_token:
             # Just warn, don't crash, maybe config is loaded differently in prod
             logger.warning("Supabase credentials not fully set in config, InfoService may fail.")
             self.supabase = None
        else:
             self.supabase = supa_client(
                str(self.supabase_url),
                str(self.supabase_anon_key),
                str(self.supabase_access_token)
            )

    def GetInfo(self, request, context):
        if not self.supabase:
             context.abort(grpc.StatusCode.INTERNAL, "Supabase client not initialized")
             return GetInfoReply()

        serial = request.serial
        try:
            # Registry Lookup
            result = (
                self.supabase.table("meter_registry")
                .select("*")
                .eq("serial", serial)
                .execute()
            )
            if len(as_list(result)) == 0:
                msg = f"meter {serial} not found"
                # Emulate emop.py behavior: print to console (server logs) and raise/abort
                logger.info(msg)
                context.abort(grpc.StatusCode.NOT_FOUND, msg)
                return GetInfoReply()

            registry_rec = as_first_item(result)

            # Shadow Lookup
            result = (
                self.supabase.table("meter_shadows")
                .select("*")
                .eq("id", registry_rec["id"])
                .execute()
            )
            shadow_rec = as_first_item(result)

            data = {"registry": registry_rec, "shadow": shadow_rec}
            # Using default=str to handle dates/decimals if any
            return GetInfoReply(json_data=json.dumps(data, indent=2, default=str))

        except Exception as e:
            logger.error(f"GetInfo failed for {serial}: {e}")
            logger.error(traceback.format_exception(e))
            context.abort(grpc.StatusCode.INTERNAL, str(e))
            return GetInfoReply()

    def GetMeters(self, request, context):
        if not self.supabase:
             context.abort(grpc.StatusCode.INTERNAL, "Supabase client not initialized")
             return GetMetersReply()

        try:
            # Replicate behavior from simt_emlite/cli/mediators.py
            result = self.supabase.rpc(
                "get_meters_for_cli", {"esco_filter": None, "feeder_filter": None}
            ).execute()

            meters = as_list(result)
            return GetMetersReply(json_meters=json.dumps(meters, indent=2, default=str))

        except Exception as e:
            logger.error(f"GetMeters failed: {e}")
            logger.error(traceback.format_exception(e))
            context.abort(grpc.StatusCode.INTERNAL, str(e))
            return GetMetersReply()
