#!/bin/bash

set -uxeo pipefail

cd $(dirname $0)/..

debian_client_archs=( amd64 i386 arm32v7 arm64v8 ppc64le s390x )

build_debian_host_image () {
  latest_tag=elijahru/distcc-cross-compiler-host-debian-buster:latest-amd64
  dockerfile=rendered/Dockerfile.distcc-cross-compiler-host-debian-buster.amd64
  docker pull $latest_tag || true
  docker build . \
    --file $dockerfile \
    --tag $latest_tag \
    --cache-from=$latest_tag
}

build_debian_client_image () {
  latest_tag=elijahru/distcc-cross-compiler-client-debian-buster:latest-$1
  dockerfile=rendered/Dockerfile.distcc-cross-compiler-client-debian-buster.$1
  docker pull $latest_tag || true
  docker build . \
    --file $dockerfile \
    --tag $latest_tag \
    --cache-from=$latest_tag
}

main () {
  ./scripts/render-templates.py
  build_debian_host_image

  for client_arch in ${debian_client_archs[@]}
  do
    build_debian_client_image $client_arch
  done

  for client_arch in ${debian_client_archs[@]}
  do
    ./scripts/run-tests-debian.sh \
      debian-buster \
      amd64 \
      debian-buster \
      $client_arch
  done
}

main
