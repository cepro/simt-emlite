"""Runs protoc with the gRPC plugin to generate messages and gRPC stubs."""

from grpc_tools import protoc

protoc.main((
    '',
    '-I.',
    '--pyi_out=./generated',
    '--python_out=./generated',
    '--grpc_python_out=./generated',
    './mediator.proto',
))
