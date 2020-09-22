#!/bin/bash

set -uxeo pipefail

declare -a pids

services=( "distccd-x86_64-linux-gnu" "distccd-i686-linux-gnu" \
           "distccd-arm-linux-gnueabihf" "distccd-aarch64-linux-gnu" \
           "distccd-powerpc64le-linux-gnu" "distccd-s390x-linux-gnu")

on_sigint () {
  echo "Interrupted..."
  for pid in ${pids[@]}
  do
    kill $pid || true
  done
}

on_sigterm () {
  echo "Terminated..."
  for pid in ${pids[@]}
  do
    kill -TERM $pid || true
  done
}

main () {
  for service in ${services[@]}
  do
    /etc/init.d/$service start
    pids+=($(cat /var/run/$service.pid))
    tail -f /var/log/$service.log 1>&2 &
    pids+=($!)
  done
  wait
}

trap on_sigint SIGINT
trap on_sigterm SIGTERM

main
