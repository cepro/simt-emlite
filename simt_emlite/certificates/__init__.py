import importlib.resources

from simt_emlite.util.config import load_config

config = load_config()


def get_cert() -> bytes:
    with importlib.resources.files(__name__).joinpath(
        f"server_cert_{config['env']}.pem"
    ).open("rb") as cert_file:
        cert_bytes = cert_file.read()
    return cert_bytes
