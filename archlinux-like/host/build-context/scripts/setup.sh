#!/bin/sh

set -uxeo pipefail

useradd distcc

# Extract cross-compiler toolchains
cd /toolchains
for file in x-tools*.tar.xz
do
  tar xf $file &
done
wait
rm -r x-tools*.tar.xz
cd -

# Whitelist binaries for specific toolchains
toolchains=( "armv5tel-unknown-linux-gnueabi" "armv6l-unknown-linux-gnueabihf" \
             "armv7l-unknown-linux-gnueabihf" "aarch64-unknown-linux-gnu")
for toolchain in ${toolchains[@]}
do
  ln -s /usr/bin/distcc /usr/lib/distcc/${toolchain}-gcc
  ln -s /usr/bin/distcc /usr/lib/distcc/${toolchain}-g++
done
