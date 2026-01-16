#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys

# Add project root to sys.path to allow importing simt_emlite modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

try:
    from simt_emlite.util.config import load_config
except ImportError:
    print("Error: Could not import simt_emlite. Make sure you are in the project root or environment is set up.")
    sys.exit(1)

def setup_mediator_mgf(esco, dry_run=False):
    app_name = f"mediator-mgf-{esco}"
    print(f"Setting up {app_name}...")

    # Load config from ~/.simt/emlite.env (or similar)
    try:
        config = load_config()
    except Exception as e:
        print(f"Warning: Could not load config: {e}")
        config = {}

    # Secrets to set.
    # Logic: Try to get from config, otherwise use placeholders.
    server_cert = config.get("MEDIATOR_SERVER_CERT", "PLACEHOLDER_SERVER_CERT_B64")
    server_key = config.get("MEDIATOR_SERVER_KEY", "PLACEHOLDER_SERVER_KEY_B64")
    ca_cert = config.get("MEDIATOR_CA_CERT", "PLACEHOLDER_CA_CERT_B64")

    secrets = {
        "MEDIATOR_SERVER_CERT": server_cert,
        "MEDIATOR_SERVER_KEY": server_key,
        "MEDIATOR_CA_CERT": ca_cert
    }

    # 1. Create App
    # We assume 'fly' CLI is installed and user is authenticated.
    cmd_create = ["fly", "apps", "create", app_name]

    print(f"Creating app {app_name} (if not exists)...")
    if dry_run:
        print(f"[DRY RUN] Would execute: {' '.join(cmd_create)}")
    else:
        # check=False because it might already exist
        result = subprocess.run(cmd_create, capture_output=True, text=True)
        if result.returncode != 0:
            if "already exists" in result.stderr or "taken" in result.stderr:
                print(f"App {app_name} already exists.")
            else:
                print(f"Error creating app: {result.stderr}")
                # We might continue or exit. Let's continue in case we just want to set secrets.

    # 2. Set Secrets
    cmd_secrets = ["fly", "secrets", "set", "--app", app_name]
    secret_args = []
    for k, v in secrets.items():
        secret_args.append(f"{k}={v}")

    cmd_secrets.extend(secret_args)

    print(f"Setting secrets for {app_name}...")
    if dry_run:
        print(f"[DRY RUN] Would execute: {' '.join(cmd_secrets[:4])} ... [secrets redacted]")
    else:
        if "PLACEHOLDER" in server_cert or "PLACEHOLDER" in server_key or "PLACEHOLDER" in ca_cert:
             print("WARNING: One or more secrets are using placeholder values. Please update them manually or in your environment config.")

        # We don't print the command as it contains secrets
        result = subprocess.run(cmd_secrets, capture_output=True, text=True)
        if result.returncode == 0:
            print("Secrets set successfully.")
        else:
            print(f"Error setting secrets: {result.stderr}")
            sys.exit(1)

    print("Setup complete.")
    print(f"Don't forget to deploy using the GitHub workflow or 'fly deploy --config fly/fly-mediator-mgf.template.toml --app {app_name}' (after generating config).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup Fly.io app and secrets for mediator-mgf services.")
    parser.add_argument("esco", help="ESCO code (e.g. wlce) to append to app name")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    args = parser.parse_args()

    setup_mediator_mgf(args.esco, args.dry_run)
