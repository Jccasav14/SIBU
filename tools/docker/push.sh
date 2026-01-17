#!/usr/bin/env bash
set -euo pipefail

SERVICE="$1"

IMAGE="jccasav/sibu-${SERVICE}"

# Tags que define el workflow
: "${DOCKER_TAG_1:?DOCKER_TAG_1 not set}"
: "${DOCKER_TAG_2:?DOCKER_TAG_2 not set}"

DOCKERFILE="apps/${SERVICE}/Dockerfile"

echo "==> Building ${IMAGE}:${DOCKER_TAG_1}"
echo "==> Building ${IMAGE}:${DOCKER_TAG_2}"

docker build -f "$DOCKERFILE" \
  -t "${IMAGE}:${DOCKER_TAG_1}" \
  -t "${IMAGE}:${DOCKER_TAG_2}" \
  .

docker push "${IMAGE}:${DOCKER_TAG_1}"
docker push "${IMAGE}:${DOCKER_TAG_2}"
