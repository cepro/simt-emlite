# Simtricity Emlite Python APIs, CLI and mediator server

[![Python test](https://github.com/cepro/simt-emlite/actions/workflows/python-test.yml/badge.svg)](https://github.com/cepro/simt-emlite/actions/workflows/python-test.yml)
[![Build and Push Docker Images](https://github.com/cepro/simt-emlite/actions/workflows/docker-image.yml/badge.svg)](https://github.com/cepro/simt-emlite/actions/workflows/docker-image.yml)

# Overview

This repository contains:

- API to connect to and send EMOP messages to Emlite meters
- a "mediator" server that talks gRPC relaying requests to the meters
- a CLI (emop) for sending messages to the meters (via the mediator servers)
- a CLI (mediators) for managing mediator servers

# CLIs

## Install and Configure

see https://www.notion.so/Emop-and-mediators-CLI-setup-834d32be5c794add8716399ab186abe8

## Use

### emop
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

### mediators
```sh
mediators list
mediators list --esco wlce      # show only mediators from the Waterlilies esco
mediators list --exists False   # show all meters that don't yet have a mediator 

mediators create EML2137580826
mediators destroy EML2137580826
mediators start EML2137580826
```

# Setup

## Local Development

see also emlite.env below

```
> python3 -m venv .venv
> source .venv/bin/activate

(.venv)> pip install -U pip setuptools
(.venv)> pip install poetry

(.venv)> poetry install
```

## emlite.env

Copy emlite.env.example to ~/.simt/emlite.env and set secrets and variables as needed.

Or once already setup you can use `mediators env_set local` to point at the local env file. 

# Tests

```
poetry run test
```

# Publish

Use account `damonrand` and publishing to test-pypi for now.

```
poetry publish --build -r test-pypi
```

# Fly Deployment

In Fly we create one Fly App per ESCO and each app has a mediator machine (container) per meter for that ESCO. An example hierarchy of apps and machines:
- mediators-wlce (Fly app)
  - mediator-EML2137580814 (machine/container)
  - mediator-EML2137580833 (machine/container)
- mediators-hmce (Fly app)
  - mediator-EML2137580900 (machine/container)
  - mediator-EML2137580901 (machine/container)

See the notes on the mediators CLI above for how to list these machines.

## Create App for ESCOs
```sh
ESCO=wlce
APP=mediators-$ESCO
fly app create $APP --org cepro
fly ips allocate-v6 --private -a $APP
```

## Create App for a single meter with TLS Auth
An alternative setup that we are trialing to expose access to a single
meter from outside of the fly cepro vpn involves deploying a single
app for a single mediator. For that setup see the section below about creating certificates and then run the following:
```sh
# lowercase letters required therefore 'eml'
SERIAL=eml123456789
APP=mediator-$SERIAL

# copy the template and edit the place holders inside
cp fly/fly-tls-auth.toml.template fly/fly-$SERIAL.toml

# create app by using lunch - no machines created at this point
fly launch --config fly/fly-$SERIAL.toml --image hello-world --no-deploy --org cepro

fly ips allocate-v4 -a $APP

# private address also created for syncer jobs running inside the private network
fly ips allocate-v6 --private -a $APP

fly secrets set MEDIATOR_SERVER_CERT="$(cat mediators-server.cert | base64 --wrap=0)"
fly secrets set MEDIATOR_SERVER_KEY="$(cat mediators-server.key | base64 --wrap=0)"
fly secrets set MEDIATOR_CA_CERT="$(cat mediators-ca.cert | base64 --wrap=0)"
```

### Create Mediator Container for either type of app
```sh
> mediators create <meter serial>
```


## Publish Docker Image to Fly

Whenever a tag is pushed the 'docker-image' github action will build and push an image to both ghcr and fly docker registries.

# gRPC

We use gRPC to generate a server and client for communication with the mediator.

The gRPC server uses the emlite-api to make calls to the meter.

## Code generation

```
cd simt_emlite/mediator/grpc
python grpc_codegen.py
```

## Authentication

Mediators use TLS certificates for authentication which is configured at the gRPC channel level.

We generate certficates for a CA, server and clients as follows.

This should be done separately for each environment - prod, qa and local.

Generated keys can be found in Lastpass under "Mediator Mutual TLS Certificates".

### CA Certificate

```sh
openssl genrsa -out mediators-ca-private.key 4096

openssl req -new -x509 \
  -key mediators-ca-private.key -sha256 \
  -subj "/C=GB/ST=England/L=Bristol/O=Cepro/CN=cepro-mediators CA" \
  -days 3650 -out mediators-ca.cert
```

### Server Certificate 

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

### Client Certificates

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

