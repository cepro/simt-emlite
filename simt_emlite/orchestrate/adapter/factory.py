import os

from simt_emlite.orchestrate.adapter.docker_adapter import DockerAdapter
from simt_emlite.orchestrate.adapter.fly_adapter import FlyAdapter

fly_api_token = os.environ.get("FLY_API_TOKEN")
fly_dns_server = os.environ.get("FLY_DNS_SERVER") or "fdaa::3"
mediator_image = os.environ.get("SIMT_EMLITE_IMAGE")


def get_instance(esco: str = None):
    if fly_api_token is not None:
        adapter = FlyAdapter(fly_api_token, fly_dns_server, mediator_image, esco)
    else:
        adapter = DockerAdapter(mediator_image)
    return adapter
