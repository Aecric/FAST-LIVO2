# syntax=docker/dockerfile:1.6
ARG ROS_DISTRO=humble
FROM ros:${ROS_DISTRO}-perception AS builder

ARG ROS_DISTRO
ARG UBUNTU_CODENAME=jammy
ARG TARGETARCH
ARG BUILD_JOBS=4
ARG VIKIT_DEB_REPO=Aecric/rpg_vikit
ARG VIKIT_DEB_TAG=v0.1.0
ARG LIVOX_DEB_REPO=Aecric/livox_ros_driver2
ARG LIVOX_DEB_TAG=1.2.6.1

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    ROS_WS=/root/fast_livo_ws

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked,id=fast-livo-apt-${TARGETARCH}-${UBUNTU_CODENAME} \
    --mount=type=cache,target=/var/lib/apt,sharing=locked,id=fast-livo-aptlib-${TARGETARCH}-${UBUNTU_CODENAME} \
    apt-get update && apt-get install -y --no-install-recommends \
      build-essential cmake fakeroot debhelper dpkg-dev devscripts \
      python3-bloom python3-rosdep \
      libboost-thread-dev libeigen3-dev libfmt-dev libopencv-dev libpcl-dev \
      ros-${ROS_DISTRO}-ament-cmake-gtest \
      ros-${ROS_DISTRO}-cv-bridge \
      ros-${ROS_DISTRO}-image-transport \
      ros-${ROS_DISTRO}-pcl-conversions \
      ros-${ROS_DISTRO}-pcl-ros \
      ros-${ROS_DISTRO}-sophus

COPY packaging/fetch_release_debs.py /usr/local/bin/fetch-release-debs

RUN set -eux; \
    ARCH="$(dpkg --print-architecture)"; \
    python3 /usr/local/bin/fetch-release-debs \
      "${VIKIT_DEB_REPO}" "${VIKIT_DEB_TAG}" \
      "^ros-${ROS_DISTRO}-vikit-(common|ros)_.*-0${UBUNTU_CODENAME}_${ARCH}\\.deb$" \
      /tmp/deps 2; \
    python3 /usr/local/bin/fetch-release-debs \
      "${LIVOX_DEB_REPO}" "${LIVOX_DEB_TAG}" \
      "^ros-${ROS_DISTRO}-livox-ros-driver2_.*-0${UBUNTU_CODENAME}_${ARCH}\\.deb$" \
      /tmp/deps 1; \
    apt-get install -y /tmp/deps/*.deb; \
    ls -lh /tmp/deps

RUN rosdep init 2>/dev/null || true && \
    rosdep update --rosdistro=${ROS_DISTRO} || \
    echo 'WARNING: rosdep update failed; build dependencies are installed explicitly'

WORKDIR ${ROS_WS}/src/FAST-LIVO2
COPY . .

RUN /bin/bash -c 'set -eo pipefail; \
    source /opt/ros/${ROS_DISTRO}/setup.bash; \
    python3 packaging/strip_private_rosdeps.py package.xml \
      livox_ros_driver2 vikit_common vikit_ros; \
    bloom-generate rosdebian \
      --os-name ubuntu \
      --os-version ${UBUNTU_CODENAME} \
      --ros-distro ${ROS_DISTRO}; \
    sed -i "s|dh_auto_configure --|dh_auto_configure -- -DFAST_LIVO_NATIVE_ARCH=OFF|" debian/rules; \
    sed -i "s|^\([[:space:]]*\)dh_auto_build$|\1dh_auto_build -- -j${BUILD_JOBS}|" debian/rules; \
    python3 packaging/inject_control_dep.py debian/control "ros-${ROS_DISTRO}-livox-ros-driver2"; \
    python3 packaging/inject_control_dep.py debian/control "ros-${ROS_DISTRO}-vikit-common"; \
    python3 packaging/inject_control_dep.py debian/control "ros-${ROS_DISTRO}-vikit-ros"; \
    export DEB_BUILD_OPTIONS=parallel=${BUILD_JOBS}; \
    fakeroot debian/rules binary'

RUN mkdir -p /output && \
    cp ${ROS_WS}/src/*.deb /output/ && \
    cp /tmp/deps/*.deb /output/ && \
    ls -lh /output

FROM scratch AS export
COPY --from=builder /output/*.deb /
