#!/usr/bin/env bash
CURRENT_DIR=`dirname "$0"`

cd $CURRENT_DIR/../..
docker build -t geotrame . -f docker/Dockerfile
cd -
