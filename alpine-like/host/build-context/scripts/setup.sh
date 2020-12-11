#!/bin/sh

set -uxeo pipefail

if [ -d /toolchaiinis ]
then
  cd /toolchains
  for file in *.tgz;
  do
    if [[ "$file" != "*.tgz" ]];
    then
      tar xzf $file;
      rm $file;
    fi;
  done
  cd -
fi
