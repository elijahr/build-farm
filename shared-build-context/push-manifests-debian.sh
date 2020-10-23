#!/bin/bash

set -uxeo pipefail

export DOCKER_CLI_EXPERIMENTAL=enabled

version=${1-}
distro=${2-}

push_distcc_host_debian () {
  manifest=elijahru/distcc-cross-compiler-host-${distro}:${version}
  tags=( \
    ${manifest}-amd64 \
    ${manifest}-i386 \
    ${manifest}-arm32v7 \
    ${manifest}-arm64v8 \
    ${manifest}-ppc64le \
    ${manifest}-s390x \
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

  docker manifest annotate \
    ${manifest} \
    ${manifest}-i386 \
    --os linux --arch 386

  docker manifest annotate \
    ${manifest} \
    ${manifest}-arm32v7 \
    --os linux --arch arm --variant v7

  docker manifest annotate \
    ${manifest} \
    ${manifest}-arm64v8 \
    --os linux --arch arm64 --variant v8

  docker manifest annotate \
    ${manifest} \
    ${manifest}-ppc64le \
    --os linux --arch ppc64le

  docker manifest annotate \
    ${manifest} \
    ${manifest}-s390x \
    --os linux --arch s390x

  docker manifest push ${manifest}
}

push_distcc_client_debian () {
  manifest=elijahru/distcc-cross-compiler-client-${distro}:${version}
  tags=( \
    ${manifest}-amd64 \
    ${manifest}-i386 \
    ${manifest}-arm32v7 \
    ${manifest}-arm64v8 \
    ${manifest}-ppc64le \
    ${manifest}-s390x \
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
    ${manifest}-i386 \
    --os linux --arch 386

  docker manifest annotate \
    ${manifest} \
    ${manifest}-arm32v7 \
    --os linux --arch arm --variant v7

  docker manifest annotate \
    ${manifest} \
    ${manifest}-arm64v8 \
    --os linux --arch arm64 --variant v8

  docker manifest annotate \
    ${manifest} \
    ${manifest}-ppc64le \
    --os linux --arch ppc64le

  docker manifest annotate \
    ${manifest} \
    ${manifest}-s390x \
    --os linux --arch s390x

  docker manifest push ${manifest}
}

push_distcc_host_archlinux () {
  manifest=elijahru/distcc-cross-compiler-host-${distro}:${version}
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

  docker manifest annotate \
    ${manifest} \
    ${manifest}-i386 \
    --os linux --arch 386

  docker manifest annotate \
    ${manifest} \
    ${manifest}-arm32v7 \
    --os linux --arch arm --variant v7

  docker manifest annotate \
    ${manifest} \
    ${manifest}-arm64v8 \
    --os linux --arch arm64 --variant v8

  docker manifest annotate \
    ${manifest} \
    ${manifest}-ppc64le \
    --os linux --arch ppc64le

  docker manifest annotate \
    ${manifest} \
    ${manifest}-s390x \
    --os linux --arch s390x

  docker manifest push ${manifest}
}

push_distcc_compiler_archlinux () {
  manifest=elijahru/distcc-cross-compiler-client-${distro}:${version}
  tags=( \
    ${manifest}-amd64 \
    ${manifest}-i386 \
    ${manifest}-arm32v7 \
    ${manifest}-arm64v8 \
    ${manifest}-ppc64le \
    ${manifest}-s390x \
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

  docker manifest push ${manifest}
}

main () {
  if [[ -z "$version" ]]
  then
    echo "Missing version argument"
    exit 1
  fi
  case $distro in
    debian*|ubuntu*)
      push_distcc_host_debian
      push_distcc_client_debian
      ;;
    archlinux*|manjaro*)
      push_distcc_host_archlinux
      push_distcc_compiler_archlinux
      ;;
    *)
      echo "Bad distro argument '$distro'"
      exit 1
      ;;
  esac
}

main
