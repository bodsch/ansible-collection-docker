# Ansible Collection - bodsch.docker

A collection of Ansible roles for docker Stuff.


## Requirements & Dependencies

- `ruamel.yaml`

```bash
pip install ruamel.yaml
```

## supported operating systems

* Arch Linux
* Debian based
    - Debian 10
    - Debian 11
    - Debian 12
    - Ubuntu 20.04
    - Ubuntu 22.04
    - Ubuntu 24.04

## Installing this collection

You can install the memsource collection with the Ansible Galaxy CLI:

```bash
#> ansible-galaxy collection install bodsch.docker
```

To install directly from GitHub:

```bash
#> ansible-galaxy collection install git@github.com:bodsch/ansible-collection-docker.git
```


You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: bodsch.docker
```

The python module dependencies are not installed by `ansible-galaxy`.  They can
be manually installed using pip:

```bash
pip install -r requirements.txt
```

## Contribution

Please read [Contribution](CONTRIBUTING.md)

## Development,  Branches (Git Tags)

The `master` Branch is my *Working Horse* includes the "latest, hot shit" and can be complete broken!

If you want to use something stable, please use a [Tagged Version](https://github.com/bodsch/ansible-collection-docker/tags)!

---

## Roles

| Role                                                         | Build State | Description |
|:----------------------------------------------------------   | :---- | :---- |
| [bodsch.docker.docker](./roles/docker/README.md)             | [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/bodsch/ansible-collection-docker/docker.yml?branch=main)][docker]             | This role will fully configure and install [dockerd](https://www.docker.com/). |
| [bodsch.docker.container](./roles/container/README.md)       | [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/bodsch/ansible-collection-docker/container.yml?branch=main)][container]       | Ansible role for deployment of generic container applications. |
| [bodsch.docker.registry](./roles/registry/README.md)         | [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/bodsch/ansible-collection-docker/registry.yml?branch=main)][registry]         | Ansible role to install and configure container [registry](https://github.com/distribution/distribution). |
| [bodsch.docker.registry_ui](./roles/registry_ui/README.md)   | [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/bodsch/ansible-collection-docker/registry-ui.yml?branch=main)][registry_ui]   | Ansible role for installing and configuring [registry-ui](https://github.com/Quiq/docker-registry-ui)  |
| [bodsch.docker.compose_file](./roles/compose_file/README.md) | [![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/bodsch/ansible-collection-docker/compose_file.yml?branch=main)][compose_file] | Ansible role to manage docker compose file or fragments. |

[docker]: https://github.com/bodsch/ansible-collection-docker/actions/workflows/docker.yml
[container]: https://github.com/bodsch/ansible-collection-docker/actions/workflows/container.yml
[registry]: https://github.com/bodsch/ansible-collection-docker/actions/workflows/registry.yml
[registry_ui]: https://github.com/bodsch/ansible-collection-docker/actions/workflows/registry-ui.yml
[compose_file]: https://github.com/bodsch/ansible-collection-docker/actions/workflows/compose_file.yml

                                                                              

## Modules

| Name                      | Description |
| :----                     | :----       |
| `compose_file`            | Manage Docker Compose YAML files |
| `compose_files`           | Manage multiple Docker Compose fragment files. |
| `container_directories`   | Manage and create container directories. |
| `container_environments`  | Manage environment and configuration files for containers.|
| `container_mounts`        | Manage and migrate container mounts and volumes. |
| `docker_client_configs`   | Manage Docker client configuration files. |
| `docker_common_config`    | Manage the Docker daemon configuration file. |
| `docker_plugins`          | Manage Docker plugins. |
| `docker_version`          | Retrieve the current Docker Engine and API version.  |

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

---

## Author

- Bodo Schulz

## License

[Apache](LICENSE)

**FREE SOFTWARE, HELL YEAH!**
