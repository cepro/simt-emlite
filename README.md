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

Because we are currently publishing to test pypi we need to run this in 2 steps
to get the main package from test pypi but all other packages from the main
pypi:

```
pip install --extra-index-url https://test.pypi.org/simple/ simt-emlite
```

## Configure

- create file ~/.simt/emlite.prod.env from Lastpass secret 'emop-cli-env-file (prod)'
- create file ~/.simt/emlite.qa.env from Lastpass secret 'emop-cli-env-file (qa)'
- ln -s ~/.simt/emlite.<qa|prod>.env ~/.simt/emlite.env
    - see `emop env_set` command for changing this after initial setup
- edit ~/.simt/emlite.env
    - set SITE=wlce|hmce|...
    - set SUPABASE_ACCESS_TOKEN

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
mediators list --full | jq
mediators list --metadata-filter "('meter_id', '9f7d7906-3980-4b6c-9714-ab1403fbd7ff')"

mediators create EML2137580826
mediators destroy_one EML2137580826
mediators start_one EML2137580826
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

## Remote mediator server

see also emlite.env below

see Notion for docs on setting up the mediator server:
https://www.notion.so/Setting-up-Emlite-meter-mediator-server-0cf0c8f97ee44843977334bc6efa86ba#658ff25657a54fbfa6388b2b42d70f66

## emlite.env

Copy emlite.env.example to ~/.simt/emlite.env and set secrets and variables as needed.

# Tests

```
poetry run test
```

# Publish

Use account `damonrand` and publishing to test-pypi for now.

```
poetry publish --build -r test-pypi
```

# Fly

## Create App
```
# TODO - add commands for creating the initial empty app

# later remove public ips and create one flycast / private ip:
APP=mediators-wlce
fly ips allocate-v6 --private -a $APP
```

## Publish Docker Image

Whenever a tag is pushed the 'docker-image' github action will build and push an image to both ghcr and fly docker registries.


# Mediator Servers

## run_mediators (soon to be deprecated)

```
bin/run_mediators --start-all
bin/run_mediators --stop-all
bin/run_mediators --remove-all
```

## cli.mediators (soon to replace run_mediators)

see examples under CLI mediators above

## Run Jobs

```
bin/run_meter_health_syncs
bin/run_meter_csq_syncs
bin/run_meter_prepay_syncs
```

# gRPC

We use gRPC to generate a server and client for communication with the mediator.

The gRPC server uses the emlite-api to make calls to the meter.

## Code generation

```
cd simt_emlite/mediator/grpc
python grpc_codegen.py
```

