#!/bin/bash

set -uxeo pipefail

export DOCKER_CLI_EXPERIMENTAL=enabled

version=${1-}

push_distcc_host () {
  manifest=elijahru/distcc-cross-compiler-host-archlinux:${version}
  tags=( \
    ${manifest}-amd64 \
  )

  for tag in ${tags[@]}
  do
    docker pull $tag || true
  done

  docker manifest create --amend \
    $manifest \
    ${tags[@]} || \
  docker manifest create \
    $manifest \
    ${tags[@]}

  docker manifest annotate \
    $manifest \
    ${manifest}-amd64 \
    --os linux --arch amd64

  docker manifest push ${manifest}
}

push_distcc_client () {
  manifest=elijahru/distcc-cross-compiler-client-archlinux:${version}
  tags=( \
    ${manifest}-amd64 \
    ${manifest}-arm32v5 \
    ${manifest}-arm32v6 \
    ${manifest}-arm32v7 \
    ${manifest}-arm64v8 \
  )

  for tag in ${tags[@]}
  do
    docker pull $tag || true
  done

  docker manifest create --amend \
    $manifest \
    ${tags[@]} || \
  docker manifest create \
    $manifest \
    ${tags[@]}

  docker manifest annotate \
    ${manifest} \
    ${manifest}-amd64 \
    --os linux --arch amd64

  docker manifest annotate \
    ${manifest} \
    ${manifest}-arm32v5 \
    --os linux --arch arm --variant v5

  docker manifest annotate \
    ${manifest} \
    ${manifest}-arm32v6 \
    --os linux --arch arm --variant v6

  docker manifest annotate \
    ${manifest} \
    ${manifest}-arm32v7 \
    --os linux --arch arm --variant v7

  docker manifest annotate \
    ${manifest} \
    ${manifest}-arm64v8 \
    --os linux --arch arm64 --variant v8

  docker manifest push ${manifest}
}

main () {
  if [[ -z "$version" ]]
  then
    echo "Missing version argument"
    exit 1
  fi
  push_distcc_host
  push_distcc_client
}

main
