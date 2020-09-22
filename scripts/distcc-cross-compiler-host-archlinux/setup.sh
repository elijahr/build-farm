#!/bin/bash

set -uxeo pipefail

for file in x-tools*.tar.xz
do
  tar xf $file &
done
wait
rm -r x-tools*.tar.xz

client_archs=( "amd64" "arm32v5" "arm32v6" "arm32v7" "arm64v8" )

for client_arch in ${client_archs[@]}
do
  systemctl disable distccd-${client_arch}.service
done
