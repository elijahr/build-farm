#!/bin/sh

set -uxe

# distcc provides gcc/g++ wrappers, but not cc, so create additional symlink
if [ -d /usr/bin/distcc/bin ]
then
  # archlinux/alpine
  ln -s /usr/bin/distcc /usr/lib/distcc/bin/cc || true
else
  # debian
  ln -s /usr/bin/distcc /usr/lib/distcc/cc || true
fi

test "$(readlink -f $(which cc))" = "$(which distcc)"
test "$(readlink -f $(which gcc))" = "$(which distcc)"
test "$(readlink -f $(which g++))" = "$(which distcc)"
