def build_app_name(is_single_meter_app: bool, serial: str | None, esco: str | None, env: str | None) -> str:
    use_env = True if env is not None and (env != "prod" and env != "qa") else False
    env_part = f"-{env}" if use_env else None

    if is_single_meter_app:
        app_name = f"mediator{env_part}-{serial}"
    elif env_part is not None:
        app_name = f"mediators{env_part}-{esco}"
    else:
        app_name = os.environ.get("FLY_APP_NAME")

    return app_name.lower()
