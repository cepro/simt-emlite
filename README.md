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

## Create App for ESCO
```sh
ESCO=xyz

# copy the template and edit the place holders inside
cp fly/fly.toml.template fly/fly-$ESCO.toml

# create app by using lunch - no machines created at this point
fly launch --config fly/fly-$ESCO.toml --no-deploy --org cepro

# allocate a public ip
fly ips allocate-v6 -a mediators-$ESCO
```

## Create Mediator Container for meter in ESCO
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

# Run mediators and sync locally

```sh
# ensure docker image built locally
bin/build-docker.sh

# start local stack with docker
cd infra/local-stack

# add mediators as needed
# NOTE: each meter added should have mode=active in flows.meter_registry
vim docker-compose.yml

# start the emnify vpn gateway and the mediators
docker compose up

# run a sync (inside the local stack docker network)
docker run --rm -it --network simt-mediator-local simt-emlite simt_emlite.jobs.meter_sync_all --esco wlce --freq daily
```
