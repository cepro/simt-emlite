#!/bin/sh

BIN_DIR=`dirname $0`
PROJECT_ROOT=`dirname $BIN_DIR`

sourceEnv() {
  . ~/.simt/emlite.env
}

runDocker() {
  MODULE=$1
  shift
  ARGS=$@
  sourceEnv
  docker run --rm \
    --name $MODULE \
	--network=host \
	--env-file ~/.simt/emlite.env \
	-v /var/run/docker.sock:/var/run/docker.sock \
	$SIMT_EMLITE_IMAGE $MODULE $ARGS
}
