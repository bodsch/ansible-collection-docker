
# Ansible Role:  `bodsch.docker.registry_ui` 

Ansible role for installing and configuring Docker [registry-ui](https://github.com/Quiq/docker-registry-ui) 
without dependencies on a container.  
Natively supports systemd and openrc as init system.

If `latest` is set for `registry_ui_version`, the role tries to install the latest release version.  
**Please use this with caution, as incompatibilities between releases may occur!**

The binaries are installed below `/usr/local/bin/registry-ui/${registry_ui_version}` and later linked to `/usr/bin`. 
This should make it possible to downgrade relatively safely.

The downloaded archive is stored on the Ansible controller, unpacked and then the binaries are copied to the target system.
The cache directory can be defined via the environment variable `CUSTOM_LOCAL_TMP_DIRECTORY`. 
By default it is `${HOME}/.cache/ansible/registry-ui`.
If this type of installation is not desired, the download can take place directly on the target system. 
However, this must be explicitly activated by setting `registry_ui_direct_download` to `true`.


## Configuration

> **Please note:** The release of the registry-ui binary is done from a fork and not from the [original](https://github.com/Quiq/docker-registry-ui), because the original repository does not provide a go-binary yet!

**ATTENTION!**

Breaking changes: Since version 0.10, the syntax of the configuration file has changed and is no longer compatible!

Here you can find the current version of the configuration: [https://github.com/bodsch/docker-registry-ui/blob/master/config.yml](config.yml)

```yaml
registry_ui_version: 0.10.3

registry_ui_release:
  download_url: https://github.com/bodsch/docker-registry-ui/releases

registry_ui_system_user: registry-ui
registry_ui_system_group: registry-ui
registry_ui_config_dir: /etc/registry-ui
registry_ui_data_dir: /var/lib/registry-ui

registry_ui_direct_download: false

registry_ui_service:
  log_level: info

registry_ui_listen:
  address: 127.0.0.1
  port: 8000

registry_ui_base_path: /

registry_ui_performance: {}

registry_ui_registry:
  hostname: "127.0.0.1:5000"
  insecure: true
  username: admin
  password: admin

registry_ui_access_control: {}

registry_ui_event_listener: {}

registry_ui_purge_tags: {}

registry_ui_debug: {}
```

### `registry_ui_listen`

Listen interface and Port

```yaml
registry_ui_listen:
  address: 127.0.0.1
  port: 8000
```

### `registry_ui_performance`

```yaml
registry_ui_performance:
  catalog_page_size: 100
  catalog_refresh_interval: 10
  tags_count_refresh_interval: 60
```

### `registry_ui_registry`

Registry URL without schema and port.

Verify TLS certificate when using https.

Docker registry credentials.  
They need to have a full access to the registry.  
If token authentication service is enabled, it will be auto-discovered and those credentials
will be used to obtain access tokens.  
When the `password_file` entry is used, the password can be passed as a docker secret
and read from file. This overides the `password` entry.

```yaml
registry_ui_registry:
  hostname: docker-registry.local
  insecure: false
  username: ""
  password: ""
  password_file: ""
  auth_with_keychain: ""
```


### `registry_ui_access_control`

```yaml
registry_ui_access_control:
  anyone_can_view_events: true
  anyone_can_delete_tags: false
  admins: []
```

### `registry_ui_event_listener`

```yaml
registry_ui_event_listener:
  bearer_token: ""
  retention_days: 7
  database:
    driver: sqlite3     #  sqlite3 or mysql
    location: ""
    username: ""
    password: ""
    hostname: 127.0.0.1:3306
    schemaname: docker_events
  deletion_enabled: true
```

### `registry_ui_purge_tags`

```yaml
registry_ui_purge_tags:
  keep_days: 90
  keep_count: 10
  keep_regexp: ''
  keep_from_file: ''
```

### `registry_ui_debug`

```yaml
registry_ui_debug:
  templates: false
```


### OBSOLETE VERSION 0.9.x

```yaml
registry_ui_version: 0.9.5

registry_ui_release_download_url: https://github.com/bodsch/docker-registry-ui/releases

registry_ui_system_user: registry-ui
registry_ui_system_group: registry-ui
registry_ui_config_dir: /etc/registry-ui
registry_ui_data_dir: /var/lib/registry-ui

registry_ui_direct_download: false

registry_ui_service:
  log_level: info

registry_ui_listen:
  address: 127.0.0.1
  port: 8000

registry_ui_base_path: /ui

registry_ui_debug: false

registry_ui_registry: {}

registry_ui_event: {}

registry_ui_cache: {}

registry_ui_admins: []

registry_ui_purge: {}
```

### `registry_ui_listen`

Listen interface and Port

```yaml
registry_ui_listen:
  address: 127.0.0.1
  port: 8000
```

### `registry_ui_registry`

Registry URL with schema and port.

Verify TLS certificate when using https.

Docker registry credentials.  
They need to have a full access to the registry.  
If token authentication service is enabled, it will be auto-discovered and those credentials
will be used to obtain access tokens.  
When the `password_file` entry is used, the password can be passed as a docker secret
and read from file. This overides the `password` entry.

```yaml
registry_ui_registry:
  url: https://docker-registry.local:5000
  verify_tls: true
  username: ""
  password: ""
  password_file: ""
```

### `registry_ui_event`

Event listener.

The same one should be configured on Docker registry as Authorization Bearer token.


```yaml
registry_ui_event:
  listener_token: ""  #  token
  retention_days: 7
  database:
    driver: sqlite3   #  sqlite3 or mysql
    location: ""      #  data/registry_events.db
    username:
    password:
    hostname: 127.0.0.1:3306
    schemaname: docker_events
  deletion_enabled: true
  anyone_can_view: true
```

### `registry_ui_cache`

```yaml
registry_ui_cache:
  refresh_interval: 10
```

### `registry_ui_admins`

```yaml
registry_ui_admins:
  anyone_can_delete: false
  admins: []
```

### `registry_ui_purge`

Enable built-in cron to schedule purging tags in server mode.  
Empty string disables this feature.  
Example: `25 54 17 * * *` will run it at 17:54:25 daily.

Note, the cron schedule format includes seconds! See [robfig/cron](https://godoc.org/github.com/robfig/cron)

```yaml
registry_ui_purge:
  tags_keep_days: 90
  tags_keep_count: 2
  tags_keep_regexp: ''
  tags_keep_from_file: ''
  tags_schedule: ''
```


---

