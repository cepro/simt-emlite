# Simtricity Emlite Python APIs, CLI and mediator server

[![Python test](https://github.com/cepro/simt-emlite/actions/workflows/python-test.yml/badge.svg)](https://github.com/cepro/simt-emlite/actions/workflows/python-test.yml)
[![Build and Push Docker Images](https://github.com/cepro/simt-emlite/actions/workflows/docker-image.yml/badge.svg)](https://github.com/cepro/simt-emlite/actions/workflows/docker-image.yml)

# Overview

This repository contains:

- API to connect to and send EMOP messages to Emlite meters
- a "mediator" server that talks to the Emlite meters relaying remote requests
  over gRPC
- a CLI for sending messages to the meters (via the mediator servers)

# Setup

## Local

```
> python3 -m venv .venv
> source .venv/bin/activate

(.venv)> pip install -U pip setuptools
(.venv)> pip install poetry

(.venv)> poetry install
```

## Remote

see Notion for docs on setting up the mediator server:
https://www.notion.so/Setting-up-Emlite-meter-mediator-server-0cf0c8f97ee44843977334bc6efa86ba#658ff25657a54fbfa6388b2b42d70f66

## Both

### Edit mediator.env

Set supabase url and key.

Set mediator docker image.

# Tests

```
poetry run test
```

# Publish

Use account `damonrand` and publishing to test-pypi for now.

```
poetry publish --build -r test-pypi
```

# CLI

## Install

Because we are currently publishing to test pyp we need to run this in 2 steps
to get the main package from test pypi but all other packages from the main
pypi:

```
pip install -i https://test.pypi.org/simple/ --no-dependencies simt-emlite
pip install --index-url https://pypi.org/simple/ --extra-index-url https://test.pypi.org/simple/ simt-emlite
```

## Use

TODO: expand this

```
poetry run emop
```

# Mediator Servers

## One mediator from Python

```
EMLITE_HOST=100.79.244.89 python -m simt_emlite.mediator.grpc.server
```

## One mediator from Docker

```
docker run --rm -it -p 50051:50051 -e EMLITE_HOST=100.79.244.89 ghcr.io/cepro/emlite-mediator:0.1.20 simt_emlite.mediator.grpc.server
```

## Start / stop / remove all mediator docker containers

```
bin/run_mediators --start-all
bin/run_mediators --stop-all
bin/run_mediators --remove-all
```

## Run Jobs

```
bin/run_meter_health_syncs
bin/run_meter_csq_syncs
bin/run_meter_prepay_syncs
```

# Client

Pass the port number of the mediator:

```
python -m simt_emlite.mediator.grpc.client 11002
```

# gRPC

We use gRPC to generate a server and client for communication with the mediator.

The gRPC server uses the emlite-api to make calls to the meter.

## Code generation

```
cd simt_emlite/mediator/grpc
python grpc_codegen.py
```
