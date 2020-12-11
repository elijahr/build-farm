#!/bin/sh

set -uxe

if [ -d /toolchains ]
then
  cd /toolchains
  for file in *.tgz
  do
    if [ "$file" != "*.tgz" ]
    then
      tar xzf $file &
    fi
  done
  wait
  for file in *.tgz
  do
    if [ "$file" != "*.tgz" ]
    then
      rm $file
    fi
  done
  cd -
fi
