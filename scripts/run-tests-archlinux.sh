#!/bin/bash

set -uxeo pipefail

host_arch=$1
client_arch=$2

docker_compose=rendered/docker-compose.host-archlinux-${host_arch}.client-archlinux-${client_arch}.yml

run_distcc_client_tests () {
  # Compile test project in the client container

  # Clear logs
  image_id=$(docker images elijahru/distcc-cross-compiler-host-archlinux:latest-${host_arch} --format "{{.ID}}")
  
  docker-compose \
    -f $docker_compose \
    up -d \
    distcc-cross-compiler-host
  sleep 5

  docker-compose \
    -f $docker_compose \
    run \
    distcc-cross-compiler-client
}

assert_distcc_host_output () {
  # Verify distcc log output from the host container
  line1=$(docker-compose -f $docker_compose logs distcc-cross-compiler-host | tail -n 2 | head -n 1)
  [[ "$line1" =~ distccd[\[0-9\]+]\ .*\ COMPILE_OK\ .*\ cJSON.c ]]

  line2=$(docker-compose -f $docker_compose logs distcc-cross-compiler-host | tail -n 1)
  [[ "$line2" =~ distccd[\[0-9\]+]\ .*\ COMPILE_OK\ .*\ cJSON_Utils.c ]]

  # Verify <= 3 compile requests were made; subsequent makes should have used ccache
  dcc_job_summary_count=$(docker-compose -f $docker_compose logs distcc-cross-compiler-host | grep -i -c dcc_job_summary)
  test "$dcc_job_summary_count" -le 2
}

main () {
  cd $(dirname $0)/..
  run_distcc_client_tests
  assert_distcc_host_output
}

on_exit () {
  docker-compose \
    -f $docker_compose \
    down
}

trap on_exit EXIT

main
