#!/usr/bin/env bash
set -euo pipefail

ROS_DISTRO="${ROS_DISTRO:-humble}"
UBUNTU_CODENAME="${UBUNTU_CODENAME:-jammy}"
TARGETARCH="${TARGETARCH:-$(dpkg --print-architecture)}"
BUILD_JOBS="${BUILD_JOBS:-4}"
VIKIT_DEB_TAG="${VIKIT_DEB_TAG:-v0.1.0}"
LIVOX_DEB_TAG="${LIVOX_DEB_TAG:-1.2.6.1}"
OUTPUT_DIR="${OUTPUT_DIR:-./debs/${ROS_DISTRO}-${TARGETARCH}}"

case "${TARGETARCH}" in
  amd64|arm64) ;;
  *) echo "unsupported TARGETARCH: ${TARGETARCH}" >&2; exit 1 ;;
esac

mkdir -p "${OUTPUT_DIR}"
docker buildx build \
  --platform "linux/${TARGETARCH}" \
  --file docker/Dockerfile \
  --target export \
  --build-arg "ROS_DISTRO=${ROS_DISTRO}" \
  --build-arg "UBUNTU_CODENAME=${UBUNTU_CODENAME}" \
  --build-arg "BUILD_JOBS=${BUILD_JOBS}" \
  --build-arg "VIKIT_DEB_TAG=${VIKIT_DEB_TAG}" \
  --build-arg "LIVOX_DEB_TAG=${LIVOX_DEB_TAG}" \
  --output "type=local,dest=${OUTPUT_DIR}" \
  --progress plain \
  .

ls -lh "${OUTPUT_DIR}"/*.deb
