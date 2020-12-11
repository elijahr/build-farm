#!/bin/bash

set -uxe

declare -a pids

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
  for service in /usr/lib/systemd/system/distccd.host-*.service
  do
    service=$(basename $service)
    systemctl start $service
    pids+=($(cat /var/run/${service}.status | sed 's/MainPID=//g'))
    tail -f /var/log/journal/${service}.log 1>&2 &
    pids+=($!)
  done
  wait
}

trap on_sigint SIGINT
trap on_sigterm SIGTERM

main
