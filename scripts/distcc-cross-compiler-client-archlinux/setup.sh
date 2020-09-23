#!/bin/bash

set -uxeo pipefail

# ccache and distcc provides gcc/g++ wrappers, but not cc, so create additional symlinks
if [[ ! -f /usr/lib/distcc/bin/cc ]]
then
  ln -s /usr/bin/distcc /usr/lib/distcc/bin/cc
fi
if [[ ! -f /usr/lib/ccache/bin/cc ]]
then
  ln -s /usr/bin/ccache /usr/lib/ccache/bin/cc
fi

# # Fix naming of compilers
# toolchains=( "armv5tel-unknown-linux-gnueabi" "armv6l-unknown-linux-gnueabihf" \
#              "armv7l-unknown-linux-gnueabihf" "aarch64-unknown-linux-gnu")
# for toolchain in ${toolchains[@]}
# do
#   rm -rf /usr/lib/ccache/bin/${toolchain}-c++
#   rm -rf /usr/lib/ccache/bin/${toolchain}-g++
#   rm -rf /usr/lib/ccache/bin/${toolchain}-gcc
# done
