#!/bin/bash
set -e

NODE_HOST=$1
CONTAINER_ID=$2

export DOCKER_HOST="tcp://$NODE_HOST:2376"
docker kill $CONTAINER_ID
