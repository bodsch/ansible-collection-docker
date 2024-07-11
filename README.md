# Ansible Collection - bodsch.docker

Documentation for the collection.

## Roles

| Role                                                       | Build State | Description |
|:---------------------------------------------------------- | :---- | :---- |
| [bodsch.docker.docker](./roles/docker/README.md)           | [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/bodsch/ansible-collection-docker/docker.yml?branch=main)][docker] | This role will fully configure and install [dockerd](https://www.docker.com/). |
| [bodsch.docker.container](./roles/container/README.md)     | [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/bodsch/ansible-collection-docker/container.yml?branch=main)][container] | Ansible role for deployment of generic container applications. |
| [bodsch.docker.registry](./roles/registry/README.md)       | [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/bodsch/ansible-collection-docker/registry.yml?branch=main)][registry] | Ansible role to install and configure container [registry](https://github.com/distribution/distribution). |
| [bodsch.docker.registry_ui](./roles/registry_ui/README.md) | [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/bodsch/ansible-collection-docker/registry-ui.yml?branch=main)][registry_ui] | Ansible role for installing and configuring [registry-ui](https://github.com/Quiq/docker-registry-ui)  |


[docker]: https://github.com/bodsch/ansible-collection-docker/actions/workflows/docker.yml
[container]: https://github.com/bodsch/ansible-collection-docker/actions/workflows/container.yml
[registry]: https://github.com/bodsch/ansible-collection-docker/actions/workflows/registry.yml
[registry_ui]: https://github.com/bodsch/ansible-collection-docker/actions/workflows/registry-ui.yml

## Modules

### ``

| Name  | Description |
| :---- | :----       |
| `container_directories`   |             |
| `container_environments`  |             |
| `container_mounts`        |             |
| `docker_client_configs`   |             |
| `docker_common_config`    |             |
| `docker_plugins`          |             |
| `docker_version`          |             |

## Filters

| Name  | Description |
| :---- | :----       |
| `container_filter`        |             |
| `container_names`         |             |
| `container_images`        |             |
| `container_state`         |             |
| `container_volumes`       |             |
| `container_mounts`        |             |
| `container_environnments` |             |
| `container_ignore_state`  |             |
| `container_with_states`   |             |
| `container_filter_by`     |             |
| `container_facts`         |             |
| `remove_custom_fields`    |             |
| `remove_source_handling`  |             |
| `changed`                 |             |
| `update`                  |             |
| `files_available`         |             |
| `reporting`               |             |
| `combine_registries`      |             |
| `validate_mountpoints`    |             |
| `validate_log_driver`     |             |
