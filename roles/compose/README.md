
# Ansible Role:  `bodsch.docker.compose`

This role will install docker compose.

## Role Variables

The following variables can be used to customize the docker installation:

```yaml
compose_version: 2.40.1

compose_install: true

compose_install_type: file # plugin | file

compose_direct_download: false

compose_scm:
  use_tags: true
  without_beta: false
  version_filter:
    - "test"
    - "preview"
    - "beta"
    - "rc"

compose_release: {}
```
