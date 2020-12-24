#!/bin/sh

set -uxe

main () {
  cd $(dirname $0)

  # TODO - this doesn't seem to actually use distcc :/
  

  # Assert that distcc wrappers are used
  test "$( (gcc 2>&1 || true) | tail -n 1 | grep distcc)" != ""
  test "$( (g++ 2>&1 || true) | tail -n 1 | grep distcc)" != ""
  test "$( (cc 2>&1 || true) | tail -n 1 | grep distcc)" != ""

  rm -Rf /tmp/cJSON
  mkdir /tmp/cJSON
  tar xzf cJSON-master.tar.gz -C /tmp/cJSON
  cd /tmp/cJSON/cJSON-master

  # Compile cJSON twice
  make clean
  make test
  make clean
  make test
  cd ~
  rm -Rf /tmp/cJSON
}

main
