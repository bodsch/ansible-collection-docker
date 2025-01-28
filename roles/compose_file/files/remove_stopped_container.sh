#!/usr/bin/env bash

container=$(docker ps --all --quiet | grep Exit | cut -d ' ' -f 1)

if [ -n "${container}" ]
then
  echo "deleting stopped containers"
  docker rm ${container}
fi
