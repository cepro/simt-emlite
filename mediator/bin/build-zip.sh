#!/bin/sh

echo "\n\nCompile and Test ...\n"
if ! mvn -o compile test; then
  exit 1
fi

echo "\n\nBuild zip ...\n"
if ! mvn -o assembly:single; then
  exit 1
fi

ZIP_FILES="bin/downloader* bin/ingester* bin/mediator* target/emoputils-0.1.1-jar-with-dependencies.jar config.*.example log4j.properties"
ZIP_FILE=target/emoputils-cli.zip
zip $ZIP_FILE $ZIP_FILES

echo "\n\nBuilt $ZIP_FILE!\n"
