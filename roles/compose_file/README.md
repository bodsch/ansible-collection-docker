
# Ansible Role:  `bodsch.docker.container`


ansible role for docker deployment of generic container applications


## Requirements & Dependencies

- pip module `ruamel.yaml`

Ansible Collections

- [bodsch.core](https://github.com/bodsch/ansible-collection-core) in Version > 1.0.14

```bash
ansible-galaxy collection install bodsch.core
```
or
```bash
ansible-galaxy collection install --requirements-file collections.yml
```

## usage

```yaml
container_reporting:
  changes: true
  failed: true

container_fail:
  error_at_launch: true

container_env_directory: /opt/container

container_registry:
  host: ''
  username: ''
  password: ''

container: []

container_pre_tasks: []
container_post_tasks: []

container_use_network: true
container_network: []

container_comparisons:
  # '*': ignore
  image: strict   # don't restart containers with older versions of the image
  env: strict     # we want precisely this environment
  labels: ignore
  
# filter container by 
container_filter:
  # ["name", "hostname", "image"]
  by: ""
  names: []
  
container_default_behavior: "compatibility"
container_clean_update_fact: true
```

### `container_reporting`

If there is a change in the started containers, a report can be issued.  
This can concern both `changes` and `failures`.

```yaml
container_reporting:
  changes: true
  failed: true
```

### `container_fail`

If there was an error when starting a container, you can define here whether you want to ignore the error.

```yaml
container_fail:
  error_at_launch: true
```

### `container_env_directory`

Defines the directory in which the environment data and the properties are persisted.

```yaml
container_env_directory: /opt/container
```


### `container registry`

Configures a container registry.  
If `host`, `username` and `password` are defined, a corresponding login to the registry is also carried out.

```yaml
container_registry:
  host: ''
  username: ''
  password: ''
```

If you need to obtain containers from more than one registry, you can also configure them accordingly (Only available from version >2.5.1):

```yaml
container_registry:
  # Log into DockerHub
  - username: 'docker'
    password: 'rekcod'
  # Log into private registry and force re-authorization
  - username: 'yourself'
    password: 'secrets3'
    host: 'your.private.registry.io'
    reauthorize: true
```

### `container_pre_tasks` and `container_post_tasks`

You can define your own pre- or post-tasks.  
The individual scripts are executed before or after (re)starting the containers.  
For example, you can use them to remove old container images, volumes or other things.  

```yaml
container_pre_tasks: []
container_post_tasks: []
```

A few example scripts can be found under [`files`](./files):

- `prune.sh`
- `list_all_container.sh`
- `list_all_images.sh`
- `remove_stopped_container.sh`
- `remove_untagged_images.sh`
- `parse_container_fact.sh`

### `container_network` / `container_use_network`

It is possible to allow the respective containers to use one (or more) network.

```yaml
container_use_network: true
container_network:
  - name: docker_network
    subnet: 172.3.27.0/24
    gateway: 172.3.27.2
    iprange: 172.3.27.0/26

  - name: monitoring
    state: absent
    enable_ipv6: false
    subnet: 172.9.27.0/24
    gateway: 172.9.27.2
    iprange: 172.9.27.0/26
```

### `container_comparisons`

The default configuration for `docker_container.comparisons`.  
Allows you to specify how properties of existing containers are compared with module options to 
decide whether or not to recreate/update the container.

[see also](https://docs.ansible.com/ansible/latest/collections/community/docker/docker_container_module.html#parameter-comparisons)

```yaml
container_comparisons:
  # '*': ignore
  image: strict   # don't restart containers with older versions of the image
  env: strict     # we want precisely this environment
  labels: ignore
```

### `container_filter`

In a large environment, there are many containers that need to be considered during a run.  
To reduce the runtime, or to roll out only certain containers, these can be filtered.
The filter criteria available here are `name`, `hostname` and `image`.

```yaml
container_filter:
  # ["name", "hostname", "image"]
  by: ""
  names: []
```

**For example:**

```yaml
container_filter:
  by: hostname
  names:
    - hello-world-1
```
or

```yaml
container_filter:
  by: image
  names:
    - busybox:latest
```


### `container_default_behavior`

> In older versions of the `docker_container` module, various module options used to have default values.  
> This caused problems with containers which use different values for these options.
> 
> The default value is now `no_defaults`.  
> To restore the old behavior, set it to `compatibility`, which will ensure that the default values are 
> used when the values are not explicitly specified by the user.
> 
> This affects the *auto_remove*, *detach*, *init*, *interactive*, *memory*, *paused*, *privileged*, *read_only* and *tty* options.

[see also](https://docs.ansible.com/ansible/latest/collections/community/docker/docker_container_module.html#parameter-container_default_behavior)

```yaml
container_default_behavior: "compatibility"
```

### `container_clean_update_fact`

To enable the necessary restart of a container over an error, a corresponding facts is created.
This fact can be evaluated in a post-task, for example.  
By default, the created fact is removed after a successful run.
For test and development purposes, the deletion can be deactivated.  

> **Please note that containers may be restarted with each new run of the role!**

```yaml
container_clean_update_fact: true
```

### `container`

A list with the definition of all containers served by this role.

> **However, not all parameters of the [`docker_container`](https://docs.ansible.com/ansible/latest/collections/community/docker/docker_container_module.html) module have been implemented!**

For all supported parameters you should have a look at [`tasks/launch/launch_container.yml`](tasks/launch/launch_container.yml).


#### Simple example:

```yaml
container:
  - name: workflow
    image: "{{ container_registry.host }}/workflow:{{ container_tag }}"
    pull: true
    state: started
    restart_policy: always
    dns_servers:
      - "{{ ansible_default_ipv4.address }}"
      networks_cli_compatible: true
      networks:
        - name: coremedia
      capabilities:
        - SYS_ADMIN
      volumes:
        - heapdumps:/coremedia/heapdumps
      published_ports:
        - 40380:8080
        - 40381:8081
        - 40383:40383
        - 40305:5005
      environments:
        DEBUG_ENTRYPOINT: "false"
        # ...
        HEAP_DUMP_FILENAME: workflow-server-heapdump
      properties:
        publisher.maxRecursionDepth: 600
```

More examples can be found here:

- [`molecule/default`](molecule/default/group_vars/all/vars.yml)
- [`molecule/multiple-containe`](molecule/multiple-container/group_vars/all/vars.yml)
- [`molecule/update-container`](molecule/update-container/group_vars/all/vars.yml)
- [`molecule/update-properties`](molecule/update-properties/group_vars/all/vars.yml)
- [`molecule/many-properties`](molecule/many-properties/group_vars/all/vars.yml)

#### environments

All `environments` entries are persisted to a separate environments file on the target system.

E.g. under `/opt/container/${CONTAINER_NAME}/container.env`

The target directory for persistence can be customized via `container_env_directory`.

#### properties

All `properties` entries are persisted to a separate properties file on the target system.

E.g. under `/opt/container/${CONTAINER_NAME}/${CONTAINER_NAME}.properties`

The target directory for persistence can be customized via `container_env_directory`.

Since version 2.3, several separate properties files can be created per container.
To do this, a list must be created under `property_files`.

> Both `properties` and `property_files` can be used in parallel.

**For example:**

```yaml

    property_files:
      - name: publisher.properties
        properties:
          # user and password for login to the staging serve
          replicator.user: 'replicator'
          replicator.password: 'replicator'
          # replicator.domain: ''
          replicator.tmp_dir: 'var/tmp'
          #
          publisher.maxRecursionDepth: 200
      - name: database.properties
```

If no `properties` is defined here, the associated file is deleted.


#### volumes and mounts

##### custom fileds for volumes

The idea behind the cutom_fields is to define corresponding rights in addition to the optional 
creation of the directories.

**For example:**

One can persist the data directory in the host system for a solr container and also assign the 
correct rights to this directory.

However, since it is also possible to mount files or sockets in the container via volumes, it is 
possible here to prevent the creation of a directory using `ignore`.

The following variables can be used:

- `owner`
- `group`
- `mode`
- `ignore`

**Example**

```yaml

    volumes:
      - /run/docker.sock:/run/docker.sock:ro
      - /tmp/nginx:/tmp/nginx:ro
      - /dev/foo:/dev/foo:ro
      - testing3:/var/tmp/testing3:rw|{owner="999",group="1000"}
      - testing4:/var/tmp/testing4|{owner="1001",mode="0700"}
```

##### custom fields for mounts

The `mounts` are similar to the `volumes`.
Here, too, it is possible to create persistent directories in the host system via an extension `source_handling`.

With `create`, you can control whether the source directory should be created or not.
The specification of `owner` and `group` enables the setting of access rights.

**Example**

```yaml

    mounts:
      - source: /tmp/testing1
        target: /var/tmp/testing1
        type: bind
        source_handling:
          create: true
          owner: "1000"
          group: "1000"
          mode: "0750"
      - source: /tmp/testing2
        target: /var/tmp/testing2
        type: bind
        source_handling:
          create: true
          owner: "800"
          group: "999"
          mode: "0700"
      - source: /tmp/testing5
        target: /var/tmp/testing5
        type: bind 
```


