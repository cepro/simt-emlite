import os

from simt_emlite.orchestrate.adapter.docker_adapter import DockerAdapter
from simt_emlite.orchestrate.adapter.fly_adapter import FlyAdapter


def get_instance(
    is_single_meter_app: bool = False,
    esco: str = None,
    serial: str = None,
    use_private_address: bool = None,
):
    # ideally load these outside the function however due to the way we load
    # the env variables in the cli tool (in the body and not before the script
    # is invoked) this module gets executed before env loading as imports are
    # above. better would be a wrapper around the cli that sets up all env
    # variables first so consider moving to that.
    fly_api_token = os.environ.get("FLY_API_TOKEN")
    fly_dns_server = os.environ.get("FLY_DNS_SERVER") or "fdaa::3"
    mediator_image = os.environ.get("SIMT_EMLITE_IMAGE")

    if fly_api_token is not None:
        print("before FlyAdapter")
        adapter = FlyAdapter(
            fly_api_token,
            fly_dns_server,
            mediator_image,
            is_single_meter_app,
            esco,
            serial,
            use_private_address,
        )
        print("after FlyAdapter")
    else:
        adapter = DockerAdapter(mediator_image)
    return adapter
