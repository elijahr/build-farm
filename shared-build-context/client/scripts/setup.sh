#!/bin/sh

set -uxe

# distcc provides gcc/g++ wrappers, but not cc, so create additional symlink
mkdir -p /usr/lib/distcc/bin
ln -s /usr/bin/distcc /usr/lib/distcc/bin/cc || true
