#!/bin/bash

set -uxeo pipefail

declare -a pids

archs=( "amd64" "arm32v5" "arm32v6" "arm32v7" "arm64v8" )

on_sigint () {
  echo "Interrupted..."
  for pid in ${pids[@]}
  do
    kill -INT $pid || true
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
  for arch in ${archs[@]}
  do
    systemctl start distccd-${arch}.service
    pids+=($(cat /var/run/distccd-${arch}.service.status | sed 's/MainPID=//g'))
    tail -f /var/log/journal/distccd-${arch}.service.log 1>&2 &
    pids+=($!)
  done
  wait
}

trap on_sigint SIGINT
trap on_sigterm SIGTERM

main
