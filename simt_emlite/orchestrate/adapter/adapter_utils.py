def build_app_name(is_single_meter_app: bool, serial: str | None, esco: str | None, env: str | None) -> str:
    use_env = True if env is not None and (env != "prod" and env != "qa") else False
    env_part = f"-{env}" if use_env else ""

    if is_single_meter_app:
        app_name = f"mediator{env_part}-{serial}"
    else:
        app_name = f"mediators{env_part}-{esco}"

    return app_name.lower()
