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

## Install

Because we are currently publishing to test pypi, add the extra index option:

```
pip install --extra-index-url https://test.pypi.org/simple/ simt-emlite
```

## Configure

- create file ~/.simt/emlite.prod.env from Lastpass secret 'emop-cli-env-file (prod)'
- create file ~/.simt/emlite.qa.env from Lastpass secret 'emop-cli-env-file (qa)'
- ln -s ~/.simt/emlite.<qa|prod>.env ~/.simt/emlite.env
    - see `emop env_set` command for changing this after initial setup
- edit ~/.simt/emlite.env
    - set SUPABASE_ACCESS_TOKEN
    - etc.

## Use

### emop
```sh 
emop env_show
emop env_set prod

emop --serial EML2137580826 --help

emop --serial EML2137580826 prepay_balance
emop --serial EML2137580826 csq
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
> ESCO=wlce
> APP=mediators-$ESCO
> fly app create $APP --org cepro
> fly ips allocate-v6 --private -a $APP
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

