import base64

def decode_b64_secret_to_bytes(b64_secret: str | None) -> bytes:
    if b64_secret is None:
        return bytes()
    return (
        base64.b64decode(b64_secret)
        .decode("utf-8")
        .replace("\\n", "\n")
        .encode("utf-8")
    )
