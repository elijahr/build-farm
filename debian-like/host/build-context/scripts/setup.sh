#!/bin/bash

# Symlink gcc, g++, etc to the cross-compilers.
# distccd will use these symlinks if /usr/local/${target}/bin is placed
# first in PATH (the etc/init.d/distccd-* scripts do this).

set -uxe

useradd --system distcc
mkdir -p /var/run/distccd
chown -R distcc:distcc /var/run/distccd

for target in "$@"
do
  mkdir -p /usr/local/${target}/bin
  files=("/usr/bin/${target}-"*)
  for file in ${files[@]}
  do
    link=/usr/local/${target}/bin/$(basename $file | sed "s/${target}-//")
    if [[ ! -f $link ]]
    then
      ln -s $file $link
    fi
  done

  # distcc provides gcc and g++ wrappers, but not cc, so create an additional symlink
  if [[ -f /usr/local/${target}/bin/cc ]]
  then
    link=/usr/local/${target}/bin/cc
    if [[ ! -f $link ]]
    then
      ln -s /usr/bin/${target}-gcc $link
    fi
  fi
done

