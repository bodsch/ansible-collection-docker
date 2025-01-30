#!/usr/bin/env bash

output() {

  while read -r line
  do
    echo -e "    $line"
  done < <(${1})

  echo ""
}

echo "- remove all stopped containers"
output "docker container prune --force"

echo "- remove all unused images, not just dangling ones"
output "docker image prune --all --force"

echo "- remove all unused networks"
output "docker network prune --force"

echo "- remove all unused local volumes. Unused local volumes are those which are not referenced by any containers"
output "docker volume prune --force"

echo "- remove all unused containers, networks, images (both dangling and unreferenced), and optionally, volumes"
output "docker system prune --all --force"
