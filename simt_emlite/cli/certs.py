#!/usr/bin/env python3
"""Certificate management CLI for mediator mTLS authentication.

This CLI provides commands to generate and manage CA, server, and client
certificates for gRPC mutual TLS authentication.

Usage:
    certs init <env>                    # Initialize CA for environment
    certs server <env>                  # Generate server certificate
    certs client <env> <client-id>      # Generate client certificate
    certs list <env>                    # List issued certificates
    certs info <cert-file>              # Display certificate details
"""

import argparse
import base64
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

# Default certificate storage location
CERTS_BASE_DIR = Path.home() / ".simt" / "certs"

# Default validity periods
CA_VALIDITY_DAYS = 3650  # 10 years
SERVER_VALIDITY_DAYS = 365  # 1 year
CLIENT_VALIDITY_DAYS = 365  # 1 year

# Default subject attributes
DEFAULT_COUNTRY = "GB"
DEFAULT_STATE = "England"
DEFAULT_LOCALITY = "Bristol"
DEFAULT_ORG = "Cepro"


def get_env_dir(env: str) -> Path:
    """Get the certificate directory for an environment."""
    return CERTS_BASE_DIR / env


def ensure_dir(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def save_key(key: rsa.RSAPrivateKey, path: Path) -> None:
    """Save private key to file."""
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    path.write_bytes(pem)
    # Restrict permissions on private key
    os.chmod(path, 0o600)
    print(f"  Saved private key: {path}")


def save_cert(cert: x509.Certificate, path: Path) -> None:
    """Save certificate to file."""
    pem = cert.public_bytes(serialization.Encoding.PEM)
    path.write_bytes(pem)
    print(f"  Saved certificate: {path}")


def load_key(path: Path) -> rsa.RSAPrivateKey:
    """Load private key from file."""
    pem = path.read_bytes()
    key = serialization.load_pem_private_key(pem, password=None)
    if not isinstance(key, rsa.RSAPrivateKey):
        raise ValueError(f"Expected RSA private key, got {type(key)}")
    return key


def load_cert(path: Path) -> x509.Certificate:
    """Load certificate from file."""
    pem = path.read_bytes()
    return x509.load_pem_x509_certificate(pem)


def to_base64(path: Path) -> str:
    """Read file and encode as base64."""
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def print_base64_output(
    key_path: Path, cert_path: Path, prefix: str, ca_path: Path | None = None
) -> None:
    """Print base64-encoded values for environment files."""
    print("\n" + "=" * 60)
    print("BASE64 ENCODED VALUES (for .env files / LastPass)")
    print("=" * 60 + "\n")

    key_b64 = to_base64(key_path)
    cert_b64 = to_base64(cert_path)

    print(f'{prefix}_KEY="{key_b64}"')
    print()
    print(f'{prefix}_CERT="{cert_b64}"')

    if ca_path:
        ca_b64 = to_base64(ca_path)
        print()
        print(f'MEDIATOR_CA_CERT="{ca_b64}"')

    print("\n" + "=" * 60 + "\n")


def update_issued_registry(
    env_dir: Path, client_id: str, cert: x509.Certificate, ou: str | None
) -> None:
    """Update the registry of issued certificates."""
    registry_path = env_dir / "issued.json"

    registry: dict[str, Any] = {}
    if registry_path.exists():
        registry = json.loads(registry_path.read_text())

    if "clients" not in registry:
        registry["clients"] = {}

    registry["clients"][client_id] = {
        "serial": format(cert.serial_number, "x"),
        "ou": ou,
        "not_before": cert.not_valid_before_utc.isoformat(),
        "not_after": cert.not_valid_after_utc.isoformat(),
        "issued_at": datetime.datetime.now(datetime.UTC).isoformat(),
    }

    registry_path.write_text(json.dumps(registry, indent=2))


# ============================================================================
# CERTIFICATE GENERATION
# ============================================================================


def generate_ca(env: str, validity_days: int = CA_VALIDITY_DAYS) -> None:
    """Generate a CA certificate for the environment."""
    env_dir = get_env_dir(env)
    ca_dir = env_dir / "ca"
    ensure_dir(ca_dir)

    key_path = ca_dir / "ca.key"
    cert_path = ca_dir / "ca.cert"

    if key_path.exists() or cert_path.exists():
        print(f"ERROR: CA already exists for environment '{env}'")
        print(f"  Key:  {key_path}")
        print(f"  Cert: {cert_path}")
        print("\nTo regenerate, first delete the existing CA files.")
        sys.exit(1)

    print(f"Generating CA for environment: {env}")

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )

    # Build certificate
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, DEFAULT_COUNTRY),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, DEFAULT_STATE),
            x509.NameAttribute(NameOID.LOCALITY_NAME, DEFAULT_LOCALITY),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, DEFAULT_ORG),
            x509.NameAttribute(NameOID.COMMON_NAME, f"cepro-mediators-{env} CA"),
        ]
    )

    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=validity_days))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=0),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_cert_sign=True,
                crl_sign=True,
                key_encipherment=False,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(private_key, hashes.SHA256())
    )

    # Save files
    save_key(private_key, key_path)
    save_cert(cert, cert_path)

    print(f"\nCA created successfully for environment: {env}")
    print(f"  Valid until: {cert.not_valid_after_utc.date()}")

    print_base64_output(key_path, cert_path, "MEDIATOR_CA")


def generate_server(env: str, validity_days: int = SERVER_VALIDITY_DAYS) -> None:
    """Generate a server certificate for the environment."""
    env_dir = get_env_dir(env)
    ca_dir = env_dir / "ca"
    server_dir = env_dir / "server"
    ensure_dir(server_dir)

    # Load CA
    ca_key_path = ca_dir / "ca.key"
    ca_cert_path = ca_dir / "ca.cert"

    if not ca_key_path.exists() or not ca_cert_path.exists():
        print(f"ERROR: CA not found for environment '{env}'")
        print(f"  Run 'certs init {env}' first to create the CA.")
        sys.exit(1)

    ca_key = load_key(ca_key_path)
    ca_cert = load_cert(ca_cert_path)

    key_path = server_dir / "server.key"
    cert_path = server_dir / "server.cert"

    print(f"Generating server certificate for environment: {env}")

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )

    # Build certificate
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, DEFAULT_COUNTRY),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, DEFAULT_STATE),
            x509.NameAttribute(NameOID.LOCALITY_NAME, DEFAULT_LOCALITY),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, DEFAULT_ORG),
            x509.NameAttribute(NameOID.COMMON_NAME, "cepro-mediators"),
        ]
    )

    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=validity_days))
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName("cepro-mediators"),
                    x509.DNSName("localhost"),
                ]
            ),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    # Save files
    save_key(private_key, key_path)
    save_cert(cert, cert_path)

    print("\nServer certificate created successfully")
    print(f"  Valid until: {cert.not_valid_after_utc.date()}")

    print_base64_output(key_path, cert_path, "MEDIATOR_SERVER", ca_cert_path)


def generate_client(
    env: str,
    client_id: str,
    ou: str | None = None,
    validity_days: int = CLIENT_VALIDITY_DAYS,
) -> None:
    """Generate a client certificate with embedded identifier."""
    env_dir = get_env_dir(env)
    ca_dir = env_dir / "ca"
    clients_dir = env_dir / "clients"
    ensure_dir(clients_dir)

    # Load CA
    ca_key_path = ca_dir / "ca.key"
    ca_cert_path = ca_dir / "ca.cert"

    if not ca_key_path.exists() or not ca_cert_path.exists():
        print(f"ERROR: CA not found for environment '{env}'")
        print(f"  Run 'certs init {env}' first to create the CA.")
        sys.exit(1)

    ca_key = load_key(ca_key_path)
    ca_cert = load_cert(ca_cert_path)

    # Sanitize client_id for filename
    safe_client_id = client_id.replace("/", "_").replace("\\", "_")
    key_path = clients_dir / f"{safe_client_id}.key"
    cert_path = clients_dir / f"{safe_client_id}.cert"

    print("Generating client certificate:")
    print(f"  Environment: {env}")
    print(f"  Client ID:   {client_id}")
    if ou:
        print(f"  Role (OU):   {ou}")

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )

    # Build subject with CN as client identifier and optional OU
    name_attrs = [
        x509.NameAttribute(NameOID.COUNTRY_NAME, DEFAULT_COUNTRY),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, DEFAULT_STATE),
        x509.NameAttribute(NameOID.LOCALITY_NAME, DEFAULT_LOCALITY),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, DEFAULT_ORG),
    ]
    if ou:
        name_attrs.append(x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, ou))
    name_attrs.append(x509.NameAttribute(NameOID.COMMON_NAME, client_id))

    subject = x509.Name(name_attrs)

    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=validity_days))
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    # Save files
    save_key(private_key, key_path)
    save_cert(cert, cert_path)

    # Update registry
    update_issued_registry(env_dir, client_id, cert, ou)

    print("\nClient certificate created successfully")
    print(f"  Valid until: {cert.not_valid_after_utc.date()}")

    print_base64_output(key_path, cert_path, "MEDIATOR_CLIENT", ca_cert_path)


def list_certs(env: str) -> None:
    """List issued certificates for an environment."""
    env_dir = get_env_dir(env)
    registry_path = env_dir / "issued.json"

    if not registry_path.exists():
        print(f"No certificates issued for environment: {env}")
        return

    registry = json.loads(registry_path.read_text())
    clients = registry.get("clients", {})

    if not clients:
        print(f"No client certificates issued for environment: {env}")
        return

    print(f"\nIssued certificates for environment: {env}")
    print("-" * 80)
    print(f"{'Client ID':<30} {'OU':<15} {'Expires':<12} {'Serial':<20}")
    print("-" * 80)

    for client_id, info in sorted(clients.items()):
        ou = info.get("ou") or "-"
        expires = info.get("not_after", "?")[:10]
        serial = info.get("serial", "?")[:16] + "..."
        print(f"{client_id:<30} {ou:<15} {expires:<12} {serial:<20}")

    print()


def show_cert_info(cert_path_str: str) -> None:
    """Display certificate details."""
    cert_path = Path(cert_path_str)

    if not cert_path.exists():
        print(f"ERROR: Certificate file not found: {cert_path}")
        sys.exit(1)

    cert = load_cert(cert_path)

    print(f"\nCertificate: {cert_path}")
    print("-" * 60)

    # Subject info
    print("Subject:")
    for attr in cert.subject:
        print(f"  {attr.oid._name}: {attr.value}")

    # Issuer info
    print("\nIssuer:")
    for attr in cert.issuer:
        print(f"  {attr.oid._name}: {attr.value}")

    # Validity
    print(f"\nValid from: {cert.not_valid_before_utc}")
    print(f"Valid until: {cert.not_valid_after_utc}")
    print(f"Serial: {format(cert.serial_number, 'x')}")

    # Extensions
    print("\nExtensions:")
    for ext in cert.extensions:
        print(f"  {ext.oid._name}: {ext.value}")

    print()


# ============================================================================
# CLI ENTRY POINT
# ============================================================================


def main() -> None:
    """Main entry point for the certs CLI."""
    parser = argparse.ArgumentParser(
        description="Certificate management for mediator mTLS authentication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  certs init prod                           # Initialize CA for prod
  certs server prod                         # Generate server certificate
  certs client prod mgf-scheduler --ou internal   # Internal client
  certs client prod partner-xyz --ou partner      # Partner client
  certs list prod                           # List issued certificates
  certs info ~/.simt/certs/prod/clients/mgf-scheduler.cert
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize CA for environment")
    init_parser.add_argument("env", help="Environment name (e.g., prod, qa, local)")
    init_parser.add_argument(
        "--days",
        type=int,
        default=CA_VALIDITY_DAYS,
        help=f"Validity period in days (default: {CA_VALIDITY_DAYS})",
    )

    # server command
    server_parser = subparsers.add_parser(
        "server", help="Generate server certificate"
    )
    server_parser.add_argument("env", help="Environment name")
    server_parser.add_argument(
        "--days",
        type=int,
        default=SERVER_VALIDITY_DAYS,
        help=f"Validity period in days (default: {SERVER_VALIDITY_DAYS})",
    )

    # client command
    client_parser = subparsers.add_parser(
        "client", help="Generate client certificate with identifier"
    )
    client_parser.add_argument("env", help="Environment name")
    client_parser.add_argument(
        "client_id", help="Client identifier (embedded as CN in certificate)"
    )
    client_parser.add_argument(
        "--ou",
        help="Organizational Unit / role (e.g., internal, partner, readonly)",
    )
    client_parser.add_argument(
        "--days",
        type=int,
        default=CLIENT_VALIDITY_DAYS,
        help=f"Validity period in days (default: {CLIENT_VALIDITY_DAYS})",
    )

    # list command
    list_parser = subparsers.add_parser(
        "list", help="List issued certificates for environment"
    )
    list_parser.add_argument("env", help="Environment name")

    # info command
    info_parser = subparsers.add_parser("info", help="Display certificate details")
    info_parser.add_argument("cert_file", help="Path to certificate file")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "init":
        generate_ca(args.env, args.days)
    elif args.command == "server":
        generate_server(args.env, args.days)
    elif args.command == "client":
        generate_client(args.env, args.client_id, args.ou, args.days)
    elif args.command == "list":
        list_certs(args.env)
    elif args.command == "info":
        show_cert_info(args.cert_file)


if __name__ == "__main__":
    main()
