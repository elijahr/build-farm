#!/bin/sh

set -uxe

mkdir -p /usr/lib/gcc-cross
cd /usr/lib/gcc-cross
for tarball in *.tar.xz
do
  if [ "$tarball" != "*.tar.xz" ]
  then
    tar xJf "$tarball" && rm "$tarball" &
  fi
done
wait

for toolchain in *
do
  if [ "$toolchain" != "*" ]
  then
    cd "${toolchain}/bin"
    for exe in ${toolchain}-*
    do
      if [ "$exe" != "${toolchain}-*" ]
      then
        # symlink toolchain to /usr/bin
        ln -s "$(readlink -f "$exe")" "/usr/bin/" || true
      fi
    done
    cd -
  fi
done
cd -

# Whitelist all compilers for use by distccd
update-distcc-symlinks
