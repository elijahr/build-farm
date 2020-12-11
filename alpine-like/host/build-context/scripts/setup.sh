#!/bin/sh

set -uxe

if [ -d /toolchains ]
then
  cd /toolchains
  for file in *.tgz
  do
    if [ "$file" != "*.tgz" ]
    then
      tar xzf $file &
    fi
  done
  wait
  for file in *.tgz
  do
    if [ "$file" != "*.tgz" ]
    then
      rm $file
    fi
  done
  for dir in *
  do
    if [ "$dir" != "*" ]
    then
      cd ${dir}/bin
      for file in *
      do
        if [ "$file" != "*" ]
        then
          # symlink toolchain binaries for whitelisting
          if [ ! -f "/usr/lib/distcc/${file}" ]
          then
            ln -s "$(readlink -f $file)" "/usr/lib/distcc/${file}"
            # alias <arch>-linux-musl-<cmd> as <arch>-alpine-linux-musl-<cmd>
            ln -s "$(readlink -f $file)" "$(dirname $(readlink -f $file))/$(echo $file | sed 's/linux/alpine-linux/')"
          fi
          if [ ! -f "/usr/lib/distcc/$(echo $file | sed 's/linux-musl/alpine-linux-musl/')" ]
          then
            # alias <arch>-linux-musl-<cmd> as <arch>-alpine-linux-musl-<cmd>
            ln -s "$(readlink -f $file)" "/usr/lib/distcc/$(echo $file | sed 's/linux/alpine-linux/')"
          fi
        fi
      done
      cd -
    fi
  done
  cd -
fi
