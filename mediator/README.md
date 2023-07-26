# Mediator

## Generate Grpc Java
Maven pom.xml is setup to generate code automatically.

It can be found in target/generated-sources/protobuf after running `mvn compile`.

## Run Server
```
export EMLITE_HOST=100.79.244.27
export EMLITE_PORT=8080
bin/mediator.sh
```

## Run Client

```
bin/mediator-client.sh
```
