#!/bin/sh

set -uxe


EXPECTED_ARCH=${1:-}

normalize_to_docker_arch () {
  # Function to detect the current running container's architecture and
  # normalize it to one of the following:
  # - amd64
  # - i386
  # - arm32v5
  # - arm32v6
  # - arm32v7
  # - arm64v8
  # - ppc
  # - ppc64le
  # - s390x
  # - mips64le

  ACTUAL_ARCH=$(uname -m)

  case $ACTUAL_ARCH in
    x86_64 | x64)
      # Detect i386 container on amd64 using __amd64 definition
      IS_AMD64=$(gcc -dM -E - < /dev/null | grep "#define __amd64 " | sed 's/#define __amd64 //')
      if [[ "$IS_AMD64" == "1" ]]
      then
        echo amd64
      else
        echo i386
      fi
      ;;
    i386 | i686 | x86)
      echo i386 ;;
    aarch64 | arm64 | armv8b | armv8l)
      echo arm64v8 ;;
    arm*)
      # Detect arm32 version using __ARM_ARCH definition
      ARM_ARCH=$(gcc -dM -E - < /dev/null | grep "#define __ARM_ARCH " | sed 's/#define __ARM_ARCH //')
      echo "arm32v$ARM_ARCH"
      ;;
    mips64)
      echo mips64le ;;
    ppc | ppc64le | s390x)
      echo $ACTUAL_ARCH ;;
    *)
      echo "Unhandled arch $ACTUAL_ARCH" 1>&2
      exit 1
      ;;
  esac
}

test "$EXPECTED_ARCH" == "$(normalize_to_docker_arch)"
