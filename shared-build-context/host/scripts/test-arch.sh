#!/bin/bash

set -uxeo pipefail

EXPECTED_ARCH=${1:-}

main () {
  if type -p dpkg &> /dev/null
  then
      ACTUAL_ARCH=$(dpkg --print-architecture)
  else
      ACTUAL_ARCH=$(uname -m)
  fi

  case $ACTUAL_ARCH in
    *amd*64* | *x86*64* | x64 )
      test "$EXPECTED_ARCH" == amd64
      ;;
    *x86* | *i*86* | x32 )
      test "$EXPECTED_ARCH" == i386
      ;;
    *aarch64* | *arm64* )
      test "$EXPECTED_ARCH" == arm64v8
      ;;
    *arm* )
      test "$EXPECTED_ARCH" == arm32v5 \
        || test "$EXPECTED_ARCH" == arm32v6 \
        || test "$EXPECTED_ARCH" == arm32v7
      ;;
    ppc64* | powerpc64* )
      test "$EXPECTED_ARCH" == ppc64le
      ;;
    *)
      echo "Unhandled arch $ACTUAL_ARCH"
      exit 1
      ;;
  esac
}

main
