#!/bin/bash
set -e

SERVICE_NAME=$1; shift

TASK_ID=$(docker service ps --filter 'desired-state=running' $SERVICE_NAME -q)
for id in ${TASK_ID}
do
    CONTAINER_ID=$(docker inspect --format '{{ .Status.ContainerStatus.ContainerID }}' $id)
    NODE_ID=$(docker inspect --format '{{ .NodeID }}' $id)
    NODE_HOST=$(docker node inspect --format '{{ .Status.Addr }}' $NODE_ID)
    export DOCKER_HOST="tcp://$NODE_HOST:2376"
    echo $(docker exec $CONTAINER_ID "$@"):$NODE_HOST
done
