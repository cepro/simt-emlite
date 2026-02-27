"""Authentication and authorization utilities for gRPC server.

This module provides:
- Client identity extraction from mTLS peer certificates
- Role-based and client-specific authorization
- gRPC interceptor for enforcing authorization on all methods
"""

import grpc
from typing import Callable, Any, Mapping
from dataclasses import dataclass

from simt_emlite.util.logging import get_logger

logger = get_logger(__name__, __file__)


@dataclass
class ClientIdentity:
    """Represents the authenticated client from certificate."""

    client_id: str  # CN from certificate (e.g., "company-xyz-api")
    role: str | None  # OU from certificate (e.g., "partner", "internal")


def extract_client_identity(context: grpc.ServicerContext) -> ClientIdentity | None:
    """
    Extract client identity (CN and OU) from peer certificate.

    gRPC exposes peer identity info via auth_context() after TLS handshake.

    Returns:
        ClientIdentity with client_id and optional role, or None if no cert auth.
    """
    auth_context = context.auth_context()
    if not auth_context:
        return None

    # Extract Common Name (client identifier)
    cn_values = auth_context.get("x509_common_name")
    if not cn_values:
        return None

    raw = cn_values[0]
    client_id_str: str
    if isinstance(raw, bytes):
        client_id_str = raw.decode("utf-8")
    elif isinstance(raw, str):
        client_id_str = raw
    else:
        client_id_str = str(raw)

    if not client_id_str:
        return None

    # Extract Organizational Unit (role) from subject
    # gRPC auth_context provides the full x509_pem_cert which we can parse
    role = _extract_ou_from_auth_context(auth_context)

    return ClientIdentity(client_id=client_id_str, role=role)


def _extract_ou_from_auth_context(auth_context: Mapping[str, Any]) -> str | None:
    """
    Extract Organizational Unit (OU) from the certificate.

    The auth_context contains 'x509_pem_cert' which we can parse to get OU.
    """
    try:
        pem_cert_list = auth_context.get("x509_pem_cert")
        if not pem_cert_list:
            return None

        pem_cert = pem_cert_list[0]
        if isinstance(pem_cert, bytes):
            pem_cert = pem_cert.decode("utf-8")

        # Parse the certificate to extract OU
        from cryptography import x509
        from cryptography.x509.oid import NameOID

        cert = x509.load_pem_x509_certificate(pem_cert.encode("utf-8"))
        ou_attrs = cert.subject.get_attributes_for_oid(NameOID.ORGANIZATIONAL_UNIT_NAME)
        if ou_attrs:
            ou_value = ou_attrs[0].value
            return str(ou_value) if ou_value is not None else None

    except Exception as e:
        logger.warning(f"Failed to extract OU from certificate: {e}")

    return None


# ============================================================================
# PERMISSION DEFINITIONS
# ============================================================================

# Define which methods each role can access
# Method names are the full gRPC method path
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "internal": {
        # Internal clients can do everything
        "/EmliteMediatorService/readElement",
        "/EmliteMediatorService/writeElement",
        "/EmliteMediatorService/sendRawMessage",
        "/InfoService/GetInfo",
        "/InfoService/GetMeters",
    },
    "partner": {
        # Partners can read from meters and get info
        "/EmliteMediatorService/readElement",
        "/InfoService/GetInfo",
        "/InfoService/GetMeters",
    },
    "readonly": {
        # Read-only access for monitoring
        "/InfoService/GetInfo",
        "/InfoService/GetMeters",
    },
}

# Override permissions for specific clients (optional)
# Use this for special cases where a specific client needs different access
# than their role would normally allow
CLIENT_PERMISSIONS: dict[str, set[str]] = {
    # Example entries - customize as needed:
    # "company-xyz-api": {
    #     "/EmliteMediatorService/readElement",
    #     "/EmliteMediatorService/writeElement",  # Special write permission
    #     "/InfoService/GetInfo",
    # },
}


def check_permission(identity: ClientIdentity, method: str) -> bool:
    """
    Check if client has permission to call the method.

    Priority:
    1. Check client-specific permissions first (overrides role)
    2. Fall back to role-based permissions
    3. Default to 'internal' role for backwards compatibility

    Args:
        identity: The authenticated client identity
        method: The full gRPC method path (e.g., "/EmliteMediatorService/readElement")

    Returns:
        True if authorized, False otherwise
    """
    # Client-specific override takes priority
    if identity.client_id in CLIENT_PERMISSIONS:
        return method in CLIENT_PERMISSIONS[identity.client_id]

    # Role-based permission
    if identity.role and identity.role in ROLE_PERMISSIONS:
        return method in ROLE_PERMISSIONS[identity.role]

    # Default: internal role for backwards compatibility
    # Existing certificates without OU will get full access
    # To change to deny-by-default, return False here instead
    logger.debug(
        f"Client {identity.client_id} has no role, using default 'internal' permissions"
    )
    return method in ROLE_PERMISSIONS.get("internal", set())


# ============================================================================
# gRPC INTERCEPTOR
# ============================================================================


class AuthorizationInterceptor(grpc.ServerInterceptor):
    """
    Server interceptor that checks client authorization before method execution.

    If authorization fails, aborts with PERMISSION_DENIED status.
    The client receives a grpc.RpcError with the denial message.
    """

    def intercept_service(
        self, continuation: Callable, handler_call_details: grpc.HandlerCallDetails
    ) -> grpc.RpcMethodHandler | None:
        """Intercept and authorize incoming requests."""
        method = handler_call_details.method

        # Get the original handler
        handler = continuation(handler_call_details)

        if handler is None:
            return handler

        # Wrap the handler to add authorization check
        return self._wrap_handler(handler, method)

    def _wrap_handler(
        self, handler: grpc.RpcMethodHandler, method: str
    ) -> grpc.RpcMethodHandler:
        """Wrap the handler with authorization logic."""
        if handler.unary_unary:
            return grpc.unary_unary_rpc_method_handler(
                self._authorize_unary(handler.unary_unary, method),
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )
        # For streaming methods, pass through without auth for now
        # Add wrappers here if streaming auth is needed
        return handler

    def _authorize_unary(
        self, original_handler: Callable, method: str
    ) -> Callable[[Any, grpc.ServicerContext], Any]:
        """Create an authorized version of the unary handler."""

        def authorized_handler(request: Any, context: grpc.ServicerContext) -> Any:
            # Extract client identity from certificate
            identity = extract_client_identity(context)

            if identity is None:
                # No certificate auth - running in insecure mode
                # Allow the request but log a warning
                logger.debug(f"No client identity for method {method} (insecure mode)")
                # For strict mode, uncomment below to require certs:
                # context.abort(
                #     grpc.StatusCode.UNAUTHENTICATED,
                #     "Client certificate required"
                # )
                # return None
            else:
                # Check authorization
                if not check_permission(identity, method):
                    logger.warning(
                        f"PERMISSION_DENIED: client={identity.client_id} "
                        f"role={identity.role} method={method}"
                    )
                    context.abort(
                        grpc.StatusCode.PERMISSION_DENIED,
                        f"Client '{identity.client_id}' is not authorized for {method}",
                    )
                    return None

                # Log successful auth at debug level
                logger.debug(
                    f"Authorized: client={identity.client_id} "
                    f"role={identity.role} method={method}"
                )

            # Call the original handler
            return original_handler(request, context)

        return authorized_handler
