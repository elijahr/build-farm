#!/bin/sh

set -uxe

if [ -d /root/x-tools ]
then
  cd /root/x-tools
  for tarball in *.tar.xz
  do
    if [ "$tarball" != "*.tar.xz" ]
    then
      tar xJf "$tarball" && rm "$tarball" &
    fi
  done
  wait
  for dir in *
  do
    if [ "$dir" != "*" ]
    then
      cd ${dir}/bin
      for file in *
      do
        if [ "$file" != "*" ]
        then
          if [ ! -f "/usr/lib/distcc/${file}" ]
          then
            # alias /root/x-tools/<toolchain>/bin/<arch>-alpine*-linux-musl*-<cmd>
            # as /usr/lib/distcc/<arch>-alpine-linux-musl*-<cmd>
            # this whitelists the binary for use with distcc and matches alpine's toolchain naming pattern
            ln -s "$(readlink -f $file)" "/usr/lib/distcc/$(echo $file | sed 's/alpine.*-linux/alpine-linux/')"
          fi
          # alias /root/x-tools/<toolchain>/bin/<arch>-alpine*-linux-musl*-<cmd>
          # as /root/x-tools/<toolchain>/bin/<cmd>
          # this allows us to set PATH and have a distccd instance default to gcc/strip/ld etc from the toolchain
          ln -s "$file" "$(echo "$file" | sed 's/.*musl[a-z]*-\(.*\)$/\1\2/')"
        fi
      done
      cd -
    fi
  done
  cd -
fi
