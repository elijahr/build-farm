#!/bin/bash

set -uxeo pipefail
shopt -s nullglob

declare -a pids

on_sigint () {
  echo "Interrupted..."
  for pid in ${pids[@]}
  do
    kill -KILL $pid || true
  done
}

on_sigterm () {
  echo "Terminated..."
  for pid in ${pids[@]}
  do
    kill -KILL $pid || true
  done
}

main () {
  echo "Starting distccd daemons"
  for service in /etc/init.d/distccd.host-*
  do
    $service start
    service_name=$(basename $service)
    pids+=($(cat /var/run/$service_name.pid))
    tail -f /var/log/$service_name.log 1>&2 &
    pids+=($!)
  done
  wait
}

trap on_sigint SIGINT
trap on_sigterm SIGTERM

main
