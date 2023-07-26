#!/bin/sh
PROJECT_ROOT=`dirname $0`/../
JAR=emoputils-0.1.0-jar-with-dependencies.jar
java -DVERBOSE=true -cp $PROJECT_ROOT:$PROJECT_ROOT/target/$JAR com.cepro.mediator.emlite.grpc.EmliteMediatorServer $@
