import os

def build_app_name(
    is_single_meter_app: bool, serial: str | None, esco: str | None, env: str | None
) -> str:
    use_env = True if env and (env != "prod" and env != "qa" and env != "bec") else False
    env_part = f"-{env}" if use_env else ""

    if is_single_meter_app:
        app_name = f"mediator{env_part}-{serial}"
    elif env is not None:
        app_name = f"mediators{env_part}-{esco}"
    else:
        fly_app_name = os.environ.get("FLY_APP_NAME")
        if fly_app_name is None:
            raise Exception("One of ENV or FLY_APP_NAME must be set")
        app_name = fly_app_name

    return app_name.lower()
