"""Runs protoc with the gRPC plugin to generate messages and gRPC stubs."""

# mypy: disable-error-code="import-untyped"
from grpc_tools import protoc

protoc.main(
    (
        "",
        "-I.",
        "--pyi_out=./generated",
        "--python_out=./generated",
        "--grpc_python_out=./generated",
        "./mediator.proto",
    )
)


def fix_imports():
    """Fixes imports in the generated code to use relative imports."""
    with open("generated/mediator_pb2_grpc.py", "r") as f:
        content = f.read()

    content = content.replace(
        "import mediator_pb2 as mediator__pb2",
        "from . import mediator_pb2 as mediator__pb2",
    )

    with open("generated/mediator_pb2_grpc.py", "w") as f:
        f.write(content)


if __name__ == "__main__":
    fix_imports()
