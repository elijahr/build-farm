#!/bin/sh

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

# Print ccache config
ccache -p
