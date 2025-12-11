import os

from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)

def build_app_name(
    is_single_meter_app: bool, serial: str | None, esco: str | None, env: str | None
) -> str:
    logger.info(f"Building app name for single meter app: {is_single_meter_app}, serial: {serial}, esco: {esco}, env: {env}")
    use_env = True if env is not None and (env != "prod" and env != "qa") else False
    env_part = f"-{env}" if use_env else ""

    if is_single_meter_app:
        app_name = f"mediator{env_part}-{serial}"
    elif env is not None:
        app_name = f"mediators{env_part}-{esco}"
    else:
        logger.info("Using FLY_APP_NAME")
        fly_app_name = os.environ.get("FLY_APP_NAME")
        if fly_app_name is None:
            raise Exception("One of ENV or FLY_APP_NAME must be set")
        app_name = fly_app_name

    logger.info(f"Built app name: {app_name}")
    return app_name.lower()
