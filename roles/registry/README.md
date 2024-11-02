
# Ansible Role:  `bodsch.docker.registry` 

Ansible role to install and configure docker [registry](https://github.com/distribution/distribution).

If `latest` is set for `registry_version`, the role tries to install the latest release version.  
**Please use this with caution, as incompatibilities between releases may occur!**

The binaries are installed below `/usr/local/bin/registry/${registry_version}` and later linked to `/usr/bin`. 
This should make it possible to downgrade relatively safely.

The downloaded archive is stored on the Ansible controller, unpacked and then the binaries are copied to the target system.
The cache directory can be defined via the environment variable `CUSTOM_LOCAL_TMP_DIRECTORY`. 
By default it is `${HOME}/.cache/ansible/registry`.
If this type of installation is not desired, the download can take place directly on the target system. 
However, this must be explicitly activated by setting `registry_direct_download` to `true`.

## Configuration

```yaml
registry_version: 2.8.1

registry_release_download_url: https://github.com/distribution/distribution/releases

registry_system_user: registry
registry_system_group: registry
registry_config_dir: /etc/docker/registry

registry_direct_download: false

registry_service: {}
registry_log: {}
registry_storage: {}
registry_auth: {}
registry_middleware: {}
registry_reporting: {}
registry_http: {}
registry_notifications: {}
registry_redis: {}
registry_health: {}
registry_proxy: {}
registry_compatibility: {}
registry_validation: {}
```

### `registry_log`

[upstream doku](https://github.com/distribution/distribution/blob/main/docs/configuration.md#log)

```yaml
registry_log:
  accesslog:
    disabled: true
  level: info
  formatter: text
  fields: {}
```

### `registry_storage`

[upstream doku](https://github.com/distribution/distribution/blob/main/docs/configuration.md#storage)
```yaml
registry_storage:
  filesystem:
    rootdirectory: /var/lib/registry
    maxthreads: 100
  delete:
    enabled: false
  cache:
    blobdescriptorsize: 10000

```

### `registry_auth`

[upstream doku](https://github.com/distribution/distribution/blob/main/docs/configuration.md#auth)
```yaml
registry_auth: {}
```

### `registry_middleware`

[upstream doku](https://github.com/distribution/distribution/blob/main/docs/configuration.md#middleware)
```yaml
registry_middleware: {}
```

### `registry_reporting`

[upstream doku](https://github.com/distribution/distribution/blob/main/docs/configuration.md#reporting)
```yaml
registry_reporting: {}
```

### `registry_http`

[upstream doku](https://github.com/distribution/distribution/blob/main/docs/configuration.md#http)
```yaml

registry_http:
  addr: localhost:5000
  secret: "{{ ansible_host | b64encode }}"
  relativeurls: true
  debug:
    addr: localhost:5001
    prometheus:
      enabled: true
      path: /metrics
```

### `registry_notifications`

[upstream doku](https://github.com/distribution/distribution/blob/main/docs/configuration.md#notifications)
```yaml
registry_notifications: {}
```

### `registry_redis`

[upstream doku](https://github.com/distribution/distribution/blob/main/docs/configuration.md#redis)
```yaml
registry_redis: {}
```

### `registry_health`

[upstream doku](https://github.com/distribution/distribution/blob/main/docs/configuration.md#health)
```yaml
registry_health: {}
```

### `registry_proxy`

[upstream doku](https://github.com/distribution/distribution/blob/main/docs/configuration.md#proxy)

```yaml
registry_proxy: {}
```

### `registry_compatibility`

[upstream doku](https://github.com/distribution/distribution/blob/main/docs/configuration.md#compatibility)
```yaml
registry_compatibility: {}
```

### `registry_validation`

[upstream doku](https://github.com/distribution/distribution/blob/main/docs/configuration.md#validation)
```yaml
registry_validation: {}
```


---

