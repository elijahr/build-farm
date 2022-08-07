#!/bin/sh

# shellcheck disable=SC1091

set -uxe

SCRIPT_DIR="$(
  cd "$(dirname "$0")" >/dev/null 2>&1
  pwd -P
)"
. "${SCRIPT_DIR}/functions.sh"

EXPECTED_ARCH=${1:-}

test "$EXPECTED_ARCH" = "$(normalize_to_docker_arch)"
