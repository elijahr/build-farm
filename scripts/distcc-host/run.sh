#!/bin/bash

declare -a pids

services=( "distccd-x86_64-linux-gnu" "distccd-i686-linux-gnu" \
           "distccd-arm-linux-gnueabihf" "distccd-aarch64-linux-gnu" \
           "distccd-powerpc64le-linux-gnu" "distccd-s390x-linux-gnu")

on_sigint () {
  echo "Interrupted..."
  for pid in ${pids[@]}
  do
    kill $pid
  done
}

on_sigterm () {
  echo "Terminated..."
  for pid in ${pids[@]}
  do
    kill -TERM $pid
  done
}

main () {
  for service in ${services[@]}
  do
    service $service start
    pids+=($(cat/var/run/$service.pid))
    tail -f /var/log/$service.log &
    pids+=($!)
  done
  wait
}

trap on_sigint SIGINT
trap on_sigterm SIGTERM

main
