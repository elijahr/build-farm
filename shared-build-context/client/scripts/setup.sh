#!/bin/sh

set -uxe

# ccache and distcc provides gcc/g++ wrappers, but not cc, so create additional symlinks
if [ -d /usr/lib/distcc/bin ]
then
  if [ ! -f /usr/lib/distcc/bin/cc ]
  then
    ln -s /usr/bin/distcc /usr/lib/distcc/bin/cc
  fi
  if [ ! -f /usr/lib/ccache/bin/cc ]
  then
    ln -s /usr/bin/ccache /usr/lib/ccache/bin/cc
  fi
else
  if [ ! -f /usr/lib/distcc/cc ]
  then
    ln -s /usr/bin/distcc /usr/lib/distcc/cc
  fi
  if [ ! -f /usr/lib/ccache/cc ]
  then
    ln -s /usr/bin/ccache /usr/lib/ccache/cc
  fi
fi

# Print ccache config
ccache -p
