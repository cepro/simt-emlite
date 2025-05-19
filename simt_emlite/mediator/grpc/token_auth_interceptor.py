from concurrent import futures
from typing import Any, Callable, List

import grpc


class TokenAuthInterceptor(grpc.ServerInterceptor):
    """A gRPC server interceptor using native APIs to validate tokens."""

    def __init__(self, valid_tokens: List[str]):
        """Initialize with a list of valid token strings.

        Args:
            valid_tokens: List of acceptable token strings.
        """
        self._valid_tokens = valid_tokens

    def intercept_service(
        self,
        continuation: Callable[[grpc.HandlerCallDetails], grpc.RpcMethodHandler],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        """Intercept gRPC service calls and validate token in metadata.

        Args:
            continuation: Function to call the next handler in the chain.
            handler_call_details: Details about the incoming call, including metadata.

        Returns:
            RpcMethodHandler if token is valid, otherwise aborts the call.
        """
        # Extract metadata
        metadata = dict(handler_call_details.invocation_metadata)
        token = metadata.get("authorization")

        if token and token in self._valid_tokens:
            # Token is valid, proceed with the call
            return continuation(handler_call_details)
        else:
            # Invalid or missing token
            return grpc.unary_unary_rpc_method_handler(
                lambda request, context: context.abort(
                    grpc.StatusCode.UNAUTHENTICATED, "Invalid or missing token"
                )
            )
