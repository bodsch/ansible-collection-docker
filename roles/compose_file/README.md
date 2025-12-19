
# Ansible Role:  `bodsch.docker.compose_file`


Ansible role to manage docker compose file or fragments.

**Work in progress**


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
compose_network: []

compose_services: []

compose_volumes: []
```

### examples

create single `compose.yml`

```yaml
- name: "compose #1"
  bodsch.docker.compose_file:
    base_directory: "/tmp/docker-compose.d"
    name: compose.yml
    state: present
    # version: 3
    networks:
      mailcow:
        driver: bridge
        driver_opts:
          com.docker.network.bridge.name: br-mailcow
        enable_ipv6: false
        ipam:
          driver: default
          config:
            - subnet: "172.22.1.0/24"

    services:
      unbound:
        image: mailcow/unbound:1.23
        restart: unless-stopped
        environment:
          - TZ=UTC
          - SKIP_UNBOUND_HEALTHCHECK=y
        volumes:
          - ./data/hooks/unbound:/hooks:Z
          - ./data/conf/unbound/unbound.conf:/etc/unbound/unbound.conf:ro,Z
        tty: true
        networks:
          mailcow:
            ipv4_address: 172.22.1.254
            aliases:
              - unbound
      memcached:
        image: memcached:alpine
        restart: unless-stopped
        environment:
          - TZ=${TZ}
        networks:
          mailcow:
            aliases:
              - memcached
    volumes:
      vmail-vol-1:
      vmail-index-vol-1:
```

#### `compose_network`

```yaml
compose_network:
  - name: mailcow
    state: present
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: br-mailcow
    enable_ipv6: false
    ipam:
      driver: default
      config:
        - subnet: ${IPV4_NETWORK:-172.22.1}.0/24
```


#### `compose_services`

```yaml
compose_services:
  - name: redis
    state: present
    image: redis:7-alpine
    entrypoint: /redis-conf.sh
    volumes:
      - ./app/redis-data:/data/
      - ./data/conf/redis/redis-conf.sh:/redis-conf.sh:z
    restart: unless-stopped
    depends_on:
      - netfilter
    ports:
      - "${REDIS_PORT:-127.0.0.1:7654}:6379"
    environment:
      - TZ=${TZ}
      - REDISPASS=${REDISPASS}
    sysctls:
      - net.core.somaxconn=4096
    networks:
      mailcow:
        ipv4_address: ${IPV4_NETWORK:-172.22.1}.249
        aliases:
          - redis
```

#### `compose_volumes`

```yaml
compose_volumes:
  - name: vmail-vol-1
    state: present
```

create multiple compose fragments

```yaml
- name: "compose #2"
  bodsch.docker.compose_files:
    base_directory: "/tmp/docker-compose.d"
    # version: 3
    networks: "{{ compose_network | default([]) }}"
    services: "{{ compose_services | default([]) }}"
    volumes: "{{ compose_volumes | default([]) }}"
```
