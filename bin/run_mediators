#!/bin/bash
#
# This script will start the "always up" set of mediator server processes.
#
# Initially this is just the landlord meters but later will be all WLCE supply
# and generation meters.
#
# This script should only need to be run once and then docker will ensure the
# containers stay up and are restarted if the host is restarted.
#
BIN_DIR=`dirname $0`
PROJECT_ROOT=$BIN_DIR/..
. $PROJECT_ROOT/mediator.env

docker run --rm -it \
	--network=host \
	--env-file mediator.env \
	-v /var/run/docker.sock:/var/run/docker.sock \
	$MEDIATOR_IMAGE emlite_mediator.orchestrate.mediators
