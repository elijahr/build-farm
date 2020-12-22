#!/bin/sh

set -uxe

# distcc provides gcc/g++ wrappers, but not cc, so create additional symlinks
if [ -d /usr/lib/distcc/bin ]
then
  if [ ! -f /usr/lib/distcc/bin/cc ]
  then
    ln -s /usr/bin/distcc /usr/lib/distcc/bin/cc
  fi
else
  if [ ! -f /usr/lib/distcc/cc ]
  then
    ln -s /usr/bin/distcc /usr/lib/distcc/cc
  fi
fi
