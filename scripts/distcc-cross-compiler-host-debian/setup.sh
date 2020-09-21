#!/bin/bash

# Symlink gcc, g++, etc to the cross-compilers.
# distccd will use these symlinks if /usr/local/${target}/bin is placed
# first in PATH (the etc/init.d/distccd-* scripts do this).

set -uxeo pipefail

targets=(
  "i686-linux-gnu" \
  "arm-linux-gnueabihf" \
  "aarch64-linux-gnu" \
  "powerpc64le-linux-gnu" \
  "s390x-linux-gnu" \
)

for target in ${targets[@]}
do
  mkdir -p /usr/local/${target}/bin
  for file in "/usr/bin/${target}-"*
  do
    ln -s $file /usr/local/${target}/bin/$(basename $file | sed "s/${target}-//")
  done

  # distcc provides gcc and g++ wrappers, but not cc, so create an additional symlink
  ln -s /usr/bin/${target}-gcc /usr/local/${target}/bin/cc

  update-rc.d distccd-${target} defaults
done

update-rc.d distccd-x86_64-linux-gnu defaults
