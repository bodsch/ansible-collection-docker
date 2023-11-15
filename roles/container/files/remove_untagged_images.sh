#!/usr/bin/env bash

container=$(docker images --all --quiet --filter dangling=true)

if [ -n "${container}" ]
then
  echo "deleting untagged images"
  docker rmi --force ${container}
fi
