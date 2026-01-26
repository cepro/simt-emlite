#!/bin/sh

BIN_DIR=`dirname $0`
PROJECT_ROOT=`dirname $BIN_DIR`

sourceEnv() {
  . ${PROJECT_ROOT}/emlite.local.env
}

runDocker() {
  MODULE=$1
  shift
  ARGS=$@
  sourceEnv
  docker run --rm \
    --name $MODULE \
	--network=host \
	--env-file ${PROJECT_ROOT}/emlite.local.env \
	-v /var/run/docker.sock:/var/run/docker.sock \
	$SIMT_EMLITE_IMAGE $MODULE $ARGS
}
