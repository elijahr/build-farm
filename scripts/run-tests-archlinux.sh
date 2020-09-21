#!/bin/bash

set -uxeo pipefail

host_arch=$1
client_arch=$2

run_distcc_client_tests () {
  # Compile test project in the client container
  docker-compose \
    -f rendered/docker-compose.host-archlinux-${host_arch}.client-archlinux-${client_arch}.yml \
    run \
    distcc-client
}

assert_distcc_host_output () {
  # Verify distcc log output from the host container
  id=$(docker ps --filter name=distcc-host --format "{{.ID}}")
  line1=$(docker exec -it $id journalctl -u distcc-{client_arch}.service | tail -n 2 | head -n 1)
  [[ "$line1" =~ distccd[\[0-9\]+]\ .*\ COMPILE_OK\ .*\ cJSON.c ]]

  line2=$(docker exec -it $id journalctl -u distcc-{client_arch}.service | tail -n 1)
  [[ "$line2" =~ distccd[\[0-9\]+]\ .*\ COMPILE_OK\ .*\ cJSON_Utils.c ]]

  # Verify only 2 compile requests were made; the second make should have used ccache
  dcc_job_summary_count=$(docker exec -it $id journalctl -u distcc-{client_arch}.service | grep -i -c dcc_job_summary)
  test "$dcc_job_summary_count" == 2
}

main () {
  cd $(dirname $0)/..
  run_distcc_client_tests
  assert_distcc_host_output
}

main
