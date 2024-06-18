# Overview
A docker compose defined stack for running mediators locally with both the access / gateway proxy and the emnify vpn proxy.

# Setup
Obtain Emnify OpenVPN credential files and drop them into the openvpn_conf/ directory.

Create the docker network for this stack:
 ```sh
docker network create simt-mediator-local
```

Start the stack:
 ```sh
docker compose up
```
