#!/usr/bin/env bash
#
# This script builds the Docker image using the current code base.
#
SCRIPT_DIR=$(cd $(dirname $0) && pwd)
PROJECT_DIR=$(cd ${SCRIPT_DIR}/.. && pwd)
DOCKER_DIR=${SCRIPT_DIR}

IMAGE_TAG="team-hipchat-bot"

pushd ${DOCKER_DIR} > /dev/null

echo "Cleaning up team-hipchat-bot..."
rm -rf team-hipchat-bot

rsync -av --exclude='docker' ${PROJECT_DIR}/* ./team-hipchat-bot
docker build --tag "${IMAGE_TAG}" .

