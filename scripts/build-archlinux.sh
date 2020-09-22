#!/bin/bash

set -uxeo pipefail

cd $(dirname $0)/..

client_archs=( "amd64" "arm32v5" "arm32v6" "arm32v7" "arm64v8" )

build_archlinux_host_image () {
  latest_tag=elijahru/distcc-cross-compiler-host-archlinux:latest-amd64
  dockerfile=rendered/Dockerfile.distcc-cross-compiler-host-archlinux.amd64
  docker pull $latest_tag || true
  docker build . \
    --file $dockerfile \
    --tag $latest_tag \
    --cache-from=$latest_tag
}

build_archlinux_client_image () {
  latest_tag=elijahru/distcc-cross-compiler-client-archlinux:latest-$1
  dockerfile=rendered/Dockerfile.distcc-cross-compiler-client-archlinux.$1
  docker pull $latest_tag || true
  docker build . \
    --file $dockerfile \
    --tag $latest_tag \
    --cache-from=$latest_tag
}

main () {
  ./scripts/render-templates.py
  build_archlinux_host_image

  for client_arch in ${client_archs[@]}
  do
    build_archlinux_client_image $client_arch
  done

  for client_arch in ${client_archs[@]}
  do
    ./scripts/run-tests-archlinux.sh \
      amd64 \
      $client_arch
  done
}

main
