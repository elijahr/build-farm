#!/bin/bash

set -uxeo pipefail

main () {
  cd $(dirname $0)

  # gcc/etc should use ccache first
  test $(which gcc) == "/usr/lib/ccache/gcc" || test $(which gcc) == "/usr/lib/ccache/bin/gcc"
  test $(which g++) == "/usr/lib/ccache/g++" || test $(which g++) == "/usr/lib/ccache/bin/g++"
  test $(which cc) == "/usr/lib/ccache/cc" || test $(which cc) == "/usr/lib/ccache/bin/cc"

  # Assert that ccache wrappers wrap distcc wrappers
  [[ "$((gcc 2>&1 || true) | tail -n 1)" =~ ^distcc[\[0-9\]+] ]]

  # Compile cJSON, will make two requests to distcc-cross-compiler-host
  rm -Rf /tmp/cJSON
  mkdir /tmp/cJSON
  tar xzf test-data/cJSON-master.tar.gz -C /tmp/cJSON
  cd /tmp/cJSON/cJSON-master

  for i in $(seq 1 4)
  do
    # Run make again, should use ccached object files instead of making requests to distcc-cross-compiler-host
    make clean
    make
    make test
  done
}

main
