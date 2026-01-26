# Simtricity Emlite Python APIs and CLI

This repository contains:

- API to connect to and send EMOP messages to Emlite meters
- a CLI (emop) for sending messages to the meters

## Configure

Configuration steps:

- create file ~/.simt/emlite.prod.env from Lastpass secret 'emop-cli-env-file (prod)'
- create file ~/.simt/emlite.qa.env from Lastpass secret 'emop-cli-env-file (qa)'
- ln -s ~/.simt/emlite.<qa|prod|custom>.env ~/.simt/emlite.env

NOTE:

- FLY_DNS_SERVER needs the DNS that wireguard uses (on Linux look under `resolvectl status` for the interface and DNS)

see also <https://www.notion.so/Emop-and-mediators-CLI-setup-834d32be5c794add8716399ab186abe8>

## Use

### emop

```sh
emop env_show
emop env_set prod

emop --help

emop prepay_balance EML2137555666
emop csq EML2137555666
emop profile_log_1 --timestamp 2024-07-19T00:00 EML2137555666
```

### Python API

You can also use the library directly in your Python scripts. The library offers two main client classes:

- `EmliteMediatorAPI`: The core client for standard meter operations (reads, basic writes).
- `EmlitePrepayAPI`: Extends the core API with prepay-specific functionality (balance, tokens, tariffs).

#### Initialization and Logging

The `EmliteMediatorAPI` constructor allows you to configure the connection and log verbosity.

```python
import logging
from simt_emlite.mediator.api_core import EmliteMediatorAPI

# Initialize the client
# The logging_level parameter controls the verbosity of the internal logger.
# It uses the standard python logging module levels (DEBUG, INFO, WARNING, ERROR).
client = EmliteMediatorAPI(
    mediator_address="localhost:50051",
    logging_level=logging.WARNING  # Set to logging.DEBUG for verbose output
)

# Example Usage
serial = "EML2137555666"
try:
    voltage = client.instantaneous_voltage(serial)
    print(f"Meter {serial} voltage: {voltage}V")
except Exception as e:
    print(f"Error: {e}")
```
