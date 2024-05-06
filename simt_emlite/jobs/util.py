import sys
import traceback
from typing import Dict
from simt_emlite.mediator.client import MediatorClientException


def update_meter_shadows_when_healthy(supabase, meter_id: str, update_properties: Dict):
    return supabase.table('meter_shadows').update({
        **update_properties,

        # clock time can be read so meter is healthy:
        "health": "healthy",
        "health_details": "",
    }).eq('id', meter_id).execute()


def handle_meter_unhealthy_status(supabase, supabase_extra, logger, meter_id: str, exception: MediatorClientException):
    logger.info(
        "updating meter_shadows.health to unhealthy")
    supabase.table('meter_shadows').update({
        "health": "unhealthy",
        "health_details": exception.message,
        "csq": None
    }).eq('id', meter_id).execute()

    if supabase_extra is not None:
        supabase_extra.table('meter_shadows').update({
            "health": "unhealthy",
            "health_details": exception.message,
            "csq": None
        }).eq('id', meter_id).execute()

    sys.exit(100)


def handle_mediator_unknown_failure(logger, error):
    logger.error(
        "failure connecting to meter or mediator", error=error)
    traceback.print_exc()
    sys.exit(101)


def handle_supabase_faliure(logger, error):
    logger.error("Supabase connection failure", error=error)
    traceback.print_exc()
    sys.exit(50)


def check_environment_vars(logger, supabase_url, supabase_key, flows_role_key, meter_id):
    if not supabase_url or not supabase_key:
        logger.error(
            "Environment variables SUPABASE_URL and SUPABASE_KEY not set.")
        sys.exit(1)

    if not flows_role_key:
        logger.error(
            "Environment variable FLOWS_ROLE_KEY not set.")
        sys.exit(2)

    if not meter_id:
        logger.error(
            "Environment variable METER_ID not set.")
        sys.exit(3)
