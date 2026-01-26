# Simtricity Emlite Python APIs, CLI and mediator server

[![Python test](https://github.com/cepro/simt-emlite/actions/workflows/python-test.yml/badge.svg)](https://github.com/cepro/simt-emlite/actions/workflows/python-test.yml)
[![Build and Push Docker Images](https://github.com/cepro/simt-emlite/actions/workflows/docker-image.yml/badge.svg)](https://github.com/cepro/simt-emlite/actions/workflows/docker-image.yml)

## Overview

This repository contains:

- API to connect to and send EMOP messages to Emlite meters
- a "mediator" server that talks gRPC relaying requests to the meters
- a CLI (emop) for sending messages to the meters (via the mediator server)

## CLIs

### Install and Configure

see <https://www.notion.so/Emop-and-mediators-CLI-setup-834d32be5c794add8716399ab186abe8>

### Use

#### emop

```sh
emop env_show
emop env_set prod

emop --help

emop csq EML2137580826
emop profile_log_1 --timestamp 2024-07-19T00:00 EML1411042768

emop prepay_balance EML2137580826
emop -s EML2244826972 prepay_send_token "99992385202946455555"

emop -s EML2244826972 tariffs_future_write --from-ts "2024-08-21T05:20:00" --unit-rate "0.175725" --standing-charge "0.503925" --ecredit-availability "10.0" --debt-recovery-rate "0.25" --emergency-credit "15.00"
```

## Scripts

### Profile Downloader

Downloads profile log 1 data for a single day from a specified meter using Supabase for meter info and connecting via the mediator client.

Usage:

```
python -m simt_emlite.cli.profile_download --serial EML1234567890 --date 2024-08-21
```

Example with config file:

```
python -m simt_emlite.cli.profile_download --config config.daily-hmce.properties
```

### Replicas Compare

Compares two replica folders containing dated CSV files, reporting files that are only in one folder or have different sizes. Optionally filter by date range.

Usage:

```
python -m simt_emlite.cli.replicas_compare <replica_dir_1> <replica_dir_2> [start_date] [end_date]
```

Examples:

```
# Compare all files in two replicas
python -m simt_emlite.cli.replicas_compare /path/to/replica1 /path/to/replica2

# Compare files within a date range
python -m simt_emlite.cli.replicas_compare /path/to/replica1 /path/to/replica2 2021-09-01 2021-09-30
```

### Replica Files Missing Records

Shell script that finds CSV files for 2025 with line counts not equal to 49, indicating missing records.

Usage:

```
./bin/replica-files-missing-records-2025 <replica_folder>
```

### Replica Check Missing

Scans a directory structure for missing daily CSV files within a specified date range, expecting files named like EML...-A-YYYYMMDD.csv in subdirectories.

Usage:

```
python -m simt_emlite.cli.replica_check_missing <root_dir> <start_date> <end_date>
```

## Setup

### Local Development

see also emlite.env below

```
> python3.13 -m venv .venv
> source .venv/bin/activate

(.venv)> pip install -U pip setuptools
(.venv)> pip install poetry

(.venv)> poetry install
```

### emlite.env

Copy emlite.env.example to ~/.simt/emlite.env and set secrets and variables as needed.

Or once already setup you can use `emop env_set local` to point at the local env file.

### Local build

build-wheels github workflow will do a cython build and publish the package so you won't need to do it locally. but if needed you can do the following (change platform if not on linux):

```sh
# setuptools build (without cibuildwheel):
python -m build

# cibuildwheel build (same as GitHub workflow):
cibuildwheel --platform linux
```

## Tests

```
poetry run test
```

## Publish

### Create App Meter Gateway

For deployments using `fly/fly-mediator-mgf.toml`:

```sh
fly launch --no-deploy --org microgridfoundry --config fly/fly-mediator-mgf.toml --name mediator-mgf

# Certificates are in lastpass or will need to be generated - see Authentication section below.
# SOCKS password also in lastpass.
fly secrets set  --config fly/fly-mediator-mgf.toml  \
    MEDIATOR_SERVER_CERT="$MEDIATOR_SERVER_CERT" \
    MEDIATOR_SERVER_KEY="$MEDIATOR_SERVER_KEY" \
    MEDIATOR_CLIENT_CERT="$MEDIATOR_CLIENT_CERT" \
    MEDIATOR_CLIENT_KEY="$MEDIATOR_CLIENT_KEY" \
    MEDIATOR_CA_CERT="$MEDIATOR_CA_CERT" \
    SOCKS_PASSWORD="$SOCKS_PASSWORD" \
    SUPABASE_ACCESS_TOKEN="$SUPABASE_ACCESS_TOKEN" \
    SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY"

fly deploy --config fly/fly-mediator-mgf.toml
fly scale count 1 --config fly/fly-mediator-mgf.toml
fly ip allocate-v6 --private -a mediator-mgf
```

#### Client certificates provided to server

Why do we do this?

It was decided to make all connections to the server secure via certificates. Initially we wanted to have an internal port exposed for the jobs like the meter sync jobs which run in an ephemeral machine inside the same fly app as the server.

But you can't get auto machine start via flycast without exposing the insecure port in [[services]] ...

An alternative to this setup would be to have the jobs in a separate app and that app has the client certificates defined and then they would not be needed in the server setup here... Time permitting I think we can move to that setup later.

#### Create Mediator Container for either type of app

```sh
> mediators create <meter serial>
```

### Publish Docker Image to Fly

Whenever a tag is pushed the 'docker-image' github action will build and push an image to both ghcr and fly docker registries.

## gRPC

We use gRPC to generate a server and client for communication with the mediator.

The gRPC server uses the emlite-api to make calls to the meter.

### Code generation

```
cd simt_emlite/mediator/grpc
python grpc_codegen.py
```

### Authentication

Mediators use TLS certificates for authentication which is configured at the gRPC channel level.

We generate certficates for a CA, server and clients as follows.

This should be done separately for each environment - prod, qa, local, custom, etc.

Generated keys can be found in Lastpass under "Mediator Mutual TLS Certificates".

#### CA Certificate

```sh
openssl genrsa -out mediators-ca-private.key 4096

openssl req -new -x509 \
  -key mediators-ca-private.key -sha256 \
  -subj "/C=GB/ST=England/L=Bristol/O=Cepro/CN=cepro-mediators CA" \
  -days 3650 -out mediators-ca.cert
```

#### Server Certificate

```sh
openssl genrsa -out mediators-server-private.key 4096

openssl req -new \
  -key mediators-server-private.key \
  -out mediators-server.csr \
  -config mediators-server-openssl.cnf

openssl x509 -req -in mediators-server.csr \
  -CA mediators-ca.cert \
  -CAkey mediators-ca-private.key \
  -CAcreateserial \
  -out mediators-server.cert \
  -days 365 -sha256 -extensions v3_ext -extfile mediators-server-openssl.cnf
```

mediators-server-openssl.cnf:

```ini
[req]
default_bits = 2048
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn

[dn]
C = GB
ST = England
L = Bristol
O = Cepro
CN = cepro-mediators

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1 = cepro-mediators

[v3_ext]
subjectAltName = @alt_names
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
```

#### Client Certificates

Generate a separate set for each external party and a set for Cepro for each environment.

```sh
openssl genrsa -out mediators-client-cepro-private.key 4096

openssl req -new \
  -key mediators-client-cepro-private.key \
  -out mediators-client-cepro.csr \
  -subj "/C=GB/ST=England/L=Bristol/O=Cepro/CN=cepro-mediators"

openssl x509 -req \
  -in mediators-client-cepro.csr \
  -CA mediators-ca.cert \
  -CAkey mediators-ca-private.key \
  -CAcreateserial \
  -out mediators-client-cepro.cert -days 365 -sha256
```
