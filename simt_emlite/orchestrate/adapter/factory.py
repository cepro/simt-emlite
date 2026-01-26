import os

from simt_emlite.orchestrate.adapter.docker_adapter import DockerAdapter
from simt_emlite.orchestrate.adapter.fly_adapter import FlyAdapter

fly_region: str | None = os.environ.get("FLY_REGION")


def get_instance(
    esco: str | None = None,
    env: str | None = None,
    serial: str | None = None,
    use_private_address: bool | None = None,
    region: str | None = fly_region,
) -> DockerAdapter | FlyAdapter:
    # ideally load these outside the function however due to the way we load
    # the env variables in the cli tool (in the body and not before the script
    # is invoked) this module gets executed before env loading as imports are
    # above. better would be a wrapper around the cli that sets up all env
    # variables first so consider moving to that.

    fly_api_token = os.environ.get("FLY_API_TOKEN")
    fly_dns_server = os.environ.get("FLY_DNS_SERVER") or "fdaa::3"
    mediator_image = os.environ.get("SIMT_EMLITE_IMAGE")

    if not mediator_image:
        raise Exception("MEDIATOR_IMAGE not set")

    adapter: DockerAdapter | FlyAdapter

    if fly_api_token is not None:
        fly_app_name = os.environ.get("FLY_APP_NAME")
        if not fly_app_name:
            raise Exception("FLY_APP_NAME environment variable must be set when using Fly")

        adapter = FlyAdapter(
            fly_api_token,
            fly_dns_server,
            mediator_image,
            fly_app_name,
            serial,
            use_private_address,
            region,
        )
    else:
        adapter = DockerAdapter(mediator_image)

    return adapter
