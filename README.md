# Ansible Collection - bodsch.docker

Documentation for the collection.

## Roles

| Role                                                       |       | Description |
|:---------------------------------------------------------- | :---- | :---- |
| [bodsch.docker.docker](./roles/docker/README.md)           |       |       |
| [bodsch.docker.container](./roles/container/README.md)     |       |       |
| [bodsch.docker.registry](./roles/registry/README.md)       |       |       |
| [bodsch.docker.registry_ui](./roles/registry_ui/README.md) |       |       |

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
