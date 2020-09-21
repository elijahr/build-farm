#!/bin/bash

set -uxeo pipefail

host_distro=$1
host_arch=$2
client_distro=$3
client_arch=$4

run_distcc_client_tests () {
  # Compile test project in the client container
  docker-compose \
    -f rendered/docker-compose.host-${host_distro}-${host_arch}.client-${client_distro}-${client_arch}.yml \
    run \
    distcc-client
}

assert_distcc_host_output () {
  # Verify distcc log output from the host container
  line1=$(docker-compose logs distcc-host | tail -n 2 | head -n 1)
  [[ "$line1" =~ distccd[\[0-9\]+]\ .*\ COMPILE_OK\ .*\ cJSON.c ]]

  line2=$(docker-compose logs distcc-host | tail -n 1)
  [[ "$line2" =~ distccd[\[0-9\]+]\ .*\ COMPILE_OK\ .*\ cJSON_Utils.c ]]

  # Verify only 2 compile requests were made; the second make should have used ccache
  dcc_job_summary_count=$(docker-compose logs distcc-host | grep -i -c dcc_job_summary)
  test "$dcc_job_summary_count" == 2
}

main () {
  cd $(dirname $0)/..
  run_distcc_client_tests
  assert_distcc_host_output
}

main
