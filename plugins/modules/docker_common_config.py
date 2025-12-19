#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2023, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
docker_common_config.py
=======================

An Ansible module for managing the Docker daemon configuration file (`/etc/docker/daemon.json`).

This module allows creating, updating, or removing Docker daemon configurations.
It ensures idempotency by comparing file checksums and provides optional diff
output to visualize configuration changes.

Features:
---------
- Create or update `/etc/docker/daemon.json` safely.
- Automatically detects configuration changes using checksums.
- Optionally generates a human-readable diff of configuration changes.
- Removes configuration files when state=absent.

This module is part of the `bodsch.docker` Ansible collection.
"""

from __future__ import absolute_import, division, print_function

import json
import os
import shutil
from typing import Any, Dict, List, Optional, Tuple

import docker
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.checksum import Checksum
from ansible_collections.bodsch.core.plugins.module_utils.diff import SideBySide
from ansible_collections.bodsch.core.plugins.module_utils.directory import (
    create_directory,
)
from ansible_collections.bodsch.core.plugins.module_utils.validate import validate

__metaclass__ = type

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
---
module: docker_common_config
author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
version_added: "1.0.0"

short_description: Manage the Docker daemon configuration file.
description:
  - This module manages the Docker daemon configuration file located at C(/etc/docker/daemon.json).
  - It supports creating, updating, or removing the configuration file in an idempotent way.
  - The module uses checksums to detect changes and can optionally display a diff between old and new configurations.
  - It validates configuration options and ensures correct JSON formatting.

options:
  state:
    description:
      - Desired state of the Docker configuration.
      - C(present) creates or updates the configuration.
      - C(absent) removes the configuration file.
    type: str
    choices: ["present", "absent"]
    default: "present"

  diff_output:
    description:
      - Whether to include a diff of the configuration changes in the output.
    type: bool
    required: false
    default: false

  data_root:
    description:
      - Directory where Docker stores its runtime data.
    type: str
    required: false

  debug:
    description:
      - Enables debug mode for the Docker daemon.
    type: bool
    required: false
    default: false

  log_driver:
    description:
      - Specifies the default logging driver for containers.
      - Supported values include C(json-file), C(syslog), C(journald), C(local), and C(loki).
    type: str
    required: false

  log_level:
    description:
      - Sets the logging level for the Docker daemon.
    type: str
    required: false
    choices: ["debug", "info", "warn", "error", "fatal"]

  log_opts:
    description:
      - A dictionary of logging options for the specified log driver.
    type: dict
    required: false

  storage_driver:
    description:
      - Defines the storage driver used by Docker.
      - Valid values include C(overlay2), C(zfs), C(btrfs), C(devicemapper), etc.
    type: str
    required: false

  storage_opts:
    description:
      - List of storage driver options.
    type: list
    required: false

  dns:
    description:
      - List of DNS servers for Docker containers.
    type: list
    required: false

  hosts:
    description:
      - List of Docker daemon host endpoints.
    type: list
    required: false

  metrics_addr:
    description:
      - Address where Docker metrics are exposed.
      - Automatically enables experimental mode when defined.
    type: str
    required: false

notes:
  - The module requires access to the Docker socket or Docker environment.
  - The Docker SDK for Python must be installed (C(pip install docker)).
  - Automatically creates the C(/etc/docker) directory if missing.

requirements:
  - Python >= 3.6
  - docker >= 4.0.0
  - bodsch.core Ansible Collection
"""

EXAMPLES = r"""
- name: create docker config file daemon.json
  bodsch.docker.docker_common_config:
    state: present
    diff_output: "{{ docker_config_diff }}"
    log_driver: "{{ docker_config.log_driver | default(omit) }}"
    log_opts: "{{ docker_config.log_opts | default(omit) }}"
    log_level: "{{ docker_config.log_level | default(omit) }}"
    dns: "{{ docker_config.dns | default(omit) }}"
    dns_opts: "{{ docker_config.dns_opts | default(omit) }}"
    dns_search: "{{ docker_config.dns_search | default(omit) }}"
    data_root: "{{ docker_config.data_root | default(omit) }}"
    max_concurrent_downloads: "{{ docker_config.max_concurrent_downloads | int | default(omit) }}"
    max_concurrent_uploads: "{{ docker_config.max_concurrent_uploads | int | default(omit) }}"
    max_download_attempts: "{{ docker_config.max_download_attempts | int | default(omit) }}"
    metrics_addr: "{{ docker_config.metrics_addr | default(omit) }}"
    debug: "{{ docker_config.debug | default('false') | bool }}"
    selinux_enabled: "{{ docker_config.selinux_enabled | default('false') | bool }}"
    seccomp_profile: "{{ docker_config.seccomp_profile | default(omit) }}"
    experimental: "{{ docker_config.experimental | default('false') | bool }}"
    storage_driver: "{{ docker_config.storage_driver | default(omit) }}"
    storage_opts: "{{ docker_config.storage_opts | default(omit) }}"
    group: "{{ docker_config.group | default(omit) }}"
    bridge: "{{ docker_config.bridge | default(omit) }}"
    bip: "{{ docker_config.bip | default(omit) }}"
    ip: "{{ docker_config.ip | default(omit) }}"
    fixed_cidr: "{{ docker_config.fixed_cidr | default(omit) }}"
    fixed_cidr_v6: "{{ docker_config.fixed_cidr_v6 | default(omit) }}"
    default_gateway: "{{ docker_config.default_gateway | default(omit) }}"
    default_gateway_v6: "{{ docker_config.default_gateway_v6 | default(omit) }}"
    hosts: "{{ docker_config.hosts | default(omit) }}"
    insecure_registries: "{{ docker_config.insecure_registries | default(omit) }}"
    shutdown_timeout: "{{ docker_config.shutdown_timeout | int | default(omit) }}"
    tls_verify: "{{ docker_config.tls.verify | default('false') | bool }}"
    tls_ca_cert: "{{ docker_config.tls.ca_cert | default(omit) }}"
    tls_cert: "{{ docker_config.tls.cert | default(omit) }}"
    tls_key: "{{ docker_config.tls.key | default(omit) }}"
  register: _changed_docker_configuration
  notify:
    - restart docker
    - information about config changes

- name: Configure Docker daemon settings
  bodsch.docker.docker_common_config:
    state: present
    data_root: /opt/docker
    max_concurrent_downloads: 10
    debug: true
    hosts:
      - unix:///var/run/docker.sock
      - tcp://0.0.0.0:3485
    fixed_cidr: "172.10.9.0/24"
    dns_search:
      - docker.local
    tls: false
    tlsverify: false
    log_driver: "json-file"
    log_opts:
      max-size: "10m"
      max-file: "3"
      mode: non-blocking
      max-buffer-size: 4m

- name: Configure metrics and DNS
  bodsch.docker.docker_common_config:
    metrics_addr: "127.0.0.1:9323"
    dns:
      - "8.8.8.8"
      - "1.1.1.1"

- name: Remove Docker configuration
  bodsch.docker.docker_common_config:
    state: absent
"""

RETURN = r"""
changed:
  description: Whether the Docker configuration file was created, updated, or deleted.
  type: bool
  returned: always
  sample: true

failed:
  description: Indicates if an error occurred during module execution.
  type: bool
  returned: always
  sample: false

msg:
  description: Human-readable message describing the action taken.
  type: str
  returned: always
  sample: "The configuration has been successfully updated."

diff:
  description: List of changes between the old and new configuration (only if diff_output=True).
  type: list
  returned: when diff_output=True
  sample:
    - "+ log-level: debug"
    - "- debug: false"
"""

# ---------------------------------------------------------------------------------------


class DockerCommonConfig(object):
    """
    Manage the Docker daemon configuration file in an idempotent way.

    This class provides functionality to create, update, validate, and remove
    the Docker daemon configuration (`/etc/docker/daemon.json`). It uses checksums
    to detect changes and optionally produces a side-by-side diff output.

    Attributes:
        module (AnsibleModule): The current Ansible module instance.
        state (str): Desired configuration state (present/absent).
        diff_output (bool): Whether to include configuration diff in the output.
        config_file (str): Path to the Docker daemon configuration file.
        checksum_file_name (str): Path to the checksum file for change detection.
        tmp_directory (str): Temporary directory used during file creation.
    """

    # Declarative parameter mapping for Docker daemon.json
    _PARAM_MAP = {
        "data_root": "data-root",
        "debug": "debug",
        "log_driver": "log-driver",
        "log_level": "log-level",
        "log_opts": "log-opts",
        "storage_driver": "storage-driver",
        "storage_opts": "storage-opts",
        "dns": "dns",
        "hosts": "hosts",
        "metrics_addr": "metrics-addr",
        "exec_opts": "exec-opts",
        "insecure_registries": "insecure-registries",
        "registry_mirrors": "registry-mirrors",
        "default_runtime": "default-runtime",
    }

    # Allowed Docker-supported values for specific options
    _ALLOWED_VALUES = {
        "log_level": ["debug", "info", "warn", "error", "fatal"],
        "log_driver": ["json-file", "syslog", "journald", "local", "loki"],
        "storage_driver": [
            "overlay2",
            "aufs",
            "zfs",
            "btrfs",
            "devicemapper",
            "vfs",
            "fuse-overlayfs",
        ],
    }

    def __init__(self, module: AnsibleModule) -> None:
        """
        Initialize module parameters and paths.


        Args:
            module (AnsibleModule): The current Ansible module instance.
        """

        self.module = module
        self.state = module.params.get("state")
        self.diff_output: bool = module.params.get("diff_output")
        #
        #
        self.authorization_plugins: List = module.params.get("authorization_plugins")
        self.bip: str = module.params.get("bip")
        self.bridge: str = module.params.get("bridge")
        self.data_root: str = module.params.get("data_root")
        self.debug: bool = module.params.get("debug")
        self.default_gateway: str = module.params.get("default_gateway")
        self.default_gateway_v6: str = module.params.get("default_gateway_v6")
        self.default_shm_size: str = module.params.get("default_shm_size")
        self.default_ulimits: str = module.params.get("default_ulimits")
        self.dns: List = module.params.get("dns")
        self.dns_opts: List = module.params.get("dns_opts")
        self.dns_search: List[str] = module.params.get("dns_search")
        self.experimental: bool = module.params.get("experimental")
        self.fixed_cidr: str = module.params.get("fixed_cidr")
        self.fixed_cidr_v6: str = module.params.get("fixed_cidr_v6")
        self.group: str = module.params.get("group")
        self.hosts: List = module.params.get("hosts")
        self.insecure_registries: List = module.params.get("insecure_registries")
        self.ip: str = module.params.get("ip")
        self.ip6tables: str = module.params.get("ip6tables")
        self.ip_forward: str = module.params.get("ip_forward")
        self.ip_masq: str = module.params.get("ip_masq")
        self.iptables: str = module.params.get("iptables")
        self.ipv6: str = module.params.get("ipv6")
        self.labels: List = module.params.get("labels")
        self.log_driver: str = module.params.get("log_driver")
        self.log_level: str = module.params.get("log_level")
        self.log_opts: Dict[str, str] = module.params.get("log_opts")
        self.max_concurrent_downloads: int = module.params.get(
            "max_concurrent_downloads"
        )
        self.max_concurrent_uploads: int = module.params.get("max_concurrent_uploads")
        self.max_download_attempts: int = module.params.get("max_download_attempts")
        self.metrics_addr: str = module.params.get("metrics_addr")
        self.oom_score_adjust: str = module.params.get("oom_score_adjust")
        self.pidfile: str = module.params.get("pidfile")
        self.raw_logs: str = module.params.get("raw_logs")
        self.registry_mirrors: List = module.params.get("registry_mirrors")
        self.seccomp_profile: str = module.params.get("seccomp_profile")
        self.selinux_enabled: bool = module.params.get("selinux_enabled")
        self.shutdown_timeout: str = module.params.get("shutdown_timeout")
        self.storage_driver: str = module.params.get("storage_driver")
        self.storage_opts: List = module.params.get("storage_opts")
        self.tls_ca_cert: str = module.params.get("tls_ca_cert")
        self.tls_cert: str = module.params.get("tls_cert")
        self.tls_key: str = module.params.get("tls_key")
        self.tls_verify: bool = module.params.get("tls_verify")

        self.config_file = "/etc/docker/daemon.json"
        # self.checksum_file_name = "/etc/docker/.checksum"

        self.cache_directory = "/var/cache/ansible/docker"
        self.checksum_file_name = os.path.join(self.cache_directory, "daemon.checksum")

        pid = os.getpid()
        self.tmp_directory = os.path.join(
            "/run/.ansible", f"docker_common_config.{str(pid)}"
        )

    def run(self) -> Dict[str, Any]:
        """
        Execute the main logic of the module.

        Returns:
            dict: Ansible result dictionary containing:
                - changed (bool): Whether a change was applied.
                - failed (bool): Whether the operation failed.
                - msg (str): Human-readable description of the result.
                - diff (list, optional): Diff output if enabled.
        """
        create_directory(self.cache_directory)
        create_directory("/etc/docker", mode="0750")

        checksum = Checksum(self.module)

        if self.state == "absent":
            """
            remove created files
            """
            if os.path.isfile(self.config_file):
                os.remove(self.config_file)

            if os.path.isfile(self.checksum_file_name):
                os.remove(self.checksum_file_name)

            return dict(changed=True, failed=False, msg="config removed")

        if not os.path.isfile(self.config_file):
            if os.path.isfile(self.checksum_file_name):
                os.remove(self.checksum_file_name)

        _diff = []

        self.__docker_client()

        data = self.config_opts()

        create_directory(directory=self.tmp_directory, mode="0750")
        tmp_file = os.path.join(self.tmp_directory, "daemon.json")
        self.__write_config(tmp_file, data)
        new_checksum = checksum.checksum_from_file(tmp_file)
        old_checksum = checksum.checksum_from_file(self.config_file)
        changed = not (new_checksum == old_checksum)
        new_file = False
        msg = "The configuration has not been changed."

        # self.module.log(f" changed       : {changed}")
        # self.module.log(f" new_checksum  : {new_checksum}")
        # self.module.log(f" old_checksum  : {old_checksum}")

        if changed:
            new_file = old_checksum is None

            if self.diff_output:
                difference = self.create_diff(self.config_file, data)
                _diff = difference

            self.__write_config(self.config_file, data)
            msg = "The configuration has been successfully updated."

        if new_file:
            msg = "The configuration was successfully created."

        shutil.rmtree(self.tmp_directory)

        return dict(changed=changed, failed=False, msg=msg, diff=_diff)

    def validate_config(self, params: Dict[str, Any]) -> None:
        """
        Validate module parameters for Docker daemon configuration.

        Ensures that all parameters are valid, correctly typed, and within
        the supported Docker configuration schema.

        Args:
            params (dict): The Ansible module parameters to validate.

        Raises:
            Calls `self.module.fail_json()` on validation failure.
        """
        # 1. Validate parameter names
        for key in params.keys():
            if key not in self._PARAM_MAP:
                self.module.fail_json(
                    msg=f"Unknown parameter '{key}' provided. Allowed keys are: {list(self._PARAM_MAP.keys())}"
                )

        # 2. Validate enumerations
        for param, allowed_values in self._ALLOWED_VALUES.items():
            value = params.get(param)

            # 3. Special case: Loki log driver requires plugin check
            if params.get("log_driver").startswith("loki"):
                self.__validate_loki_plugin()
                continue

            if validate(value) and value not in allowed_values:
                self.module.fail_json(
                    msg=f"Invalid value '{value}' for parameter '{param}'. "
                    f"Allowed values are: {allowed_values}"
                )

        # 4. Type validation
        if params.get("log_opts") and not isinstance(params["log_opts"], dict):
            self.module.fail_json(msg="Parameter 'log_opts' must be a dictionary.")

        if params.get("storage_opts") and not isinstance(params["storage_opts"], list):
            self.module.fail_json(msg="Parameter 'storage_opts' must be a list.")

        if params.get("dns") and not isinstance(params["dns"], list):
            self.module.fail_json(msg="Parameter 'dns' must be a list of strings.")

        if params.get("hosts") and not isinstance(params["hosts"], list):
            self.module.fail_json(msg="Parameter 'hosts' must be a list of strings.")

        # 5. Cross-field validation
        if params.get("metrics_addr"):
            params["experimental"] = True

        # 6. Sanity check for paths
        if params.get("data_root") and not os.path.isabs(params["data_root"]):
            self.module.fail_json(
                msg=f"Parameter 'data_root' must be an absolute path: {params['data_root']}"
            )

        self.module.log(msg="Docker configuration parameters validated successfully.")

    def config_opts(self) -> Dict[str, Any]:
        """
        Build a validated Docker daemon configuration dictionary.

        Collects all supported module parameters, validates them,
        and maps them to their corresponding Docker daemon configuration keys.

        Returns:
            dict: Validated configuration data ready to be written to JSON.
        """
        params = {key: self.module.params.get(key) for key in self._PARAM_MAP.keys()}

        # 1. Validate parameters before building the configuration
        self.validate_config(params)

        config: Dict[str, Any] = {}
        for param, docker_key in self._PARAM_MAP.items():
            value = params.get(param)

            if not validate(value):
                continue

            if isinstance(value, dict):
                value = self.__values_as_string(value)

            config[docker_key] = value

        if "metrics-addr" in config:
            config["experimental"] = True

        return config

    # ----------------------------------------------------------------------

    def __validate_loki_plugin(self) -> None:
        """
        Verify that the Loki Docker log driver plugin is installed and enabled.

        This function connects to the Docker daemon using the Docker SDK
        and searches for the `grafana/loki-docker-driver` plugin.

        If the plugin is not installed or disabled, the module fails gracefully
        with a clear message.

        Raises:
            Calls `self.module.fail_json()` if the plugin is missing or disabled.
        """
        try:
            docker_socket = "/var/run/docker.sock"
            if os.path.exists(docker_socket):
                client = docker.DockerClient(base_url=f"unix://{docker_socket}")
            else:
                client = docker.from_env()

            plugins = client.plugins.list()

            for plugin in plugins:
                self.module.log(f"  - {plugin}")

                plugin_enabled = plugin.enabled
                plugin_name = plugin.name
                plugin_shortname = plugin.name.split(":")[0]
                plugin_version = plugin.name.split(":")[1]

                if plugin_name and plugin_version:
                    msg = f"plugin {plugin_shortname} is installed in version '{plugin_version}'"

                    if not plugin_enabled:
                        self.module.fail_json(
                            msg="Loki plugin 'grafana/loki-docker-driver' is installed but not enabled. "
                            "Please enable it using 'docker plugin enable grafana/loki-docker-driver'."
                        )

                    if not self.log_driver == plugin_name:
                        msg += ", but versions are not equal!"

                    self.module.log(msg)
                    return

            # If loop completes without returning, plugin not found
            self.module.fail_json(
                msg="Required Loki Docker log driver plugin not found. "
                "Install it using: 'docker plugin install grafana/loki-docker-driver:latest --alias loki --grant-all-permissions'."
            )

        except (docker.errors.DockerException, docker.errors.APIError) as e:
            self.module.fail_json(
                msg=f"Unable to verify Loki plugin installation: {str(e)}"
            )

    def create_diff(self, config_file: str, data: Dict[str, Any]) -> list:
        """
        Generate a side-by-side diff of old and new Docker configurations.

        Args:
            config_file (str): Path to the existing configuration file.
            data (dict): New configuration data.

        Returns:
            list: A formatted list of diff lines showing changes.
        """
        old_data = dict()

        if os.path.isfile(config_file):
            with open(config_file) as json_file:
                old_data = json.load(json_file)

        side_by_side = SideBySide(self.module, old_data, data)
        diff_side_by_side = side_by_side.diff(
            width=140, left_title="  Original", right_title="  Update"
        )

        return diff_side_by_side

    def __values_as_string(self, values: Dict[str, Any]) -> Dict[str, str]:
        """
        Convert all dictionary values to strings to ensure compatibility with Docker JSON schema.

        Args:
            values (dict): Dictionary of key-value pairs (e.g., logging options).

        Returns:
            dict: Converted dictionary with all values represented as strings.
        """
        result = {}
        # self.module.log(msg=f"{json.dumps(values, indent=2, sort_keys=False)}")

        if isinstance(values, dict):
            for k, v in sorted(values.items()):
                if isinstance(v, bool):
                    v = str(v).lower()
                result[k] = str(v)

        # self.module.log(msg=f"{json.dumps(result, indent=2, sort_keys=False)}")

        return result

    def __docker_client(self) -> Optional[Dict[str, Any]]:
        """
        Initialize the Docker SDK client to communicate with the Docker daemon.

        Attempts to connect via `/var/run/docker.sock`, or falls back to environment
        configuration if the socket is unavailable.

        Returns:
            dict or None: Result dictionary if an error occurs, otherwise None.
        """
        docker_status = False
        docker_socket = "/var/run/docker.sock"
        # TODO
        # with broken ~/.docker/daemon.json will this fail!
        try:
            if os.path.exists(docker_socket):
                # self.module.log("use docker.sock")
                self.docker_client = docker.DockerClient(
                    base_url=f"unix://{docker_socket}"
                )
            else:
                self.docker_client = docker.from_env()

            docker_status = self.docker_client.ping()
        except docker.errors.APIError as e:
            self.module.log(msg=f" exception: {e}")
        except Exception as e:
            self.module.log(msg=f" exception: {e}")

        if not docker_status:
            return dict(changed=False, failed=True, msg="no running docker found")

    def __check_plugin(self) -> Tuple[bool, str]:
        """
        Check whether a required Docker plugin (e.g., for log drivers) is installed.

        Returns:
            tuple:
                bool: Whether the plugin is valid and matches the requested version.
                str: Human-readable status message describing the result.
        """
        installed_plugin_name = None
        installed_plugin_shortname = None
        installed_plugin_version = None
        installed_plugin_enabled = None

        plugin_valid = False

        msg = f"plugin {self.log_driver} ist not installed"

        try:
            p_list = self.docker_client.plugins.list()

            for plugin in p_list:

                installed_plugin_enabled = plugin.enabled

                if installed_plugin_enabled:
                    installed_plugin_name = plugin.name
                    installed_plugin_shortname = plugin.name.split(":")[0]
                    installed_plugin_version = plugin.name.split(":")[1]

                    break

        except docker.errors.APIError as e:
            error = str(e)
            self.module.log(msg=f"{error}")

        except Exception as e:
            error = str(e)
            self.module.log(msg=f"{error}")

        if installed_plugin_name and installed_plugin_version:
            msg = f"plugin {installed_plugin_shortname} is installed in version '{installed_plugin_version}'"

            if self.log_driver == installed_plugin_name:
                plugin_valid = True
            else:
                plugin_valid = False
                msg += ", but versions are not equal!"

            return plugin_valid, msg
        else:
            return plugin_valid, msg

    def __write_config(self, file_name: str, data: Dict[str, Any]) -> None:
        """
        Write the Docker configuration data to a JSON file.

        Args:
            file_name (str): Destination file path.
            data (dict): Configuration data to write.
        """
        with open(file_name, "w") as fp:
            json_data = json.dumps(data, indent=2, sort_keys=False)
            fp.write(f"{json_data}\n")

    # ---

    def _config_opts(self) -> Dict[str, Any]:
        """
        Build a validated Docker daemon configuration dictionary.

        This method collects all supported module parameters, validates them,
        and maps them to their corresponding Docker daemon configuration keys.
        It skips undefined or invalid values automatically.

        Additionally, it validates certain keys such as C(log_level),
        C(log_driver), and C(storage_driver) against allowed Docker values.

        Returns:
            dict: Validated configuration data ready to be written to JSON.
        """

        # Mapping of Ansible module parameters to Docker daemon JSON keys
        key_map = {
            "data_root": "data-root",
            "debug": "debug",
            "log_driver": "log-driver",
            "log_level": "log-level",
            "log_opts": "log-opts",
            "storage_driver": "storage-driver",
            "storage_opts": "storage-opts",
            "dns": "dns",
            "hosts": "hosts",
            "metrics_addr": "metrics-addr",
            "exec_opts": "exec-opts",
            "insecure_registries": "insecure-registries",
            "registry_mirrors": "registry-mirrors",
            "default_runtime": "default-runtime",
        }

        # Explicit Docker-supported values for selected keys
        allowed_values = {
            "log_level": ["debug", "info", "warn", "error", "fatal"],
            "log_driver": ["json-file", "syslog", "journald", "local", "loki"],
            "storage_driver": [
                "overlay2",
                "aufs",
                "zfs",
                "btrfs",
                "devicemapper",
                "vfs",
                "fuse-overlayfs",
            ],
        }

        config: Dict[str, Any] = {}

        for param_name, docker_key in key_map.items():
            value = self.module.params.get(param_name)

            # Skip undefined or invalid values
            if not validate(value):
                continue

            # Validate Docker-supported enumerations
            if param_name in allowed_values and value not in allowed_values[param_name]:
                self.module.fail_json(
                    msg=f"Invalid value '{value}' for parameter '{param_name}'. "
                    f"Allowed values are: {allowed_values[param_name]}"
                )

            # Convert nested dicts (like log_opts) to strings
            if isinstance(value, dict):
                value = self.__values_as_string(value)

            config[docker_key] = value

        # Automatically enable experimental mode if metrics_addr is defined
        if "metrics-addr" in config:
            config["experimental"] = True

        return config

    def __OLD_config_opts(self) -> Dict[str, Any]:
        """
        Build a validated dictionary of Docker daemon configuration options.

        Reads all supported module parameters and validates them before including
        them in the resulting JSON structure. Unsupported or undefined values are ignored.

        Returns:
            dict: Valid configuration data ready to be written as JSON.
        """

        data = dict()

        if validate(self.authorization_plugins):
            data["authorization-plugins"] = self.authorization_plugins

        if validate(self.bip):
            data["bip"] = self.bip

        if validate(self.bridge):
            data["bridge"] = self.bridge

        if validate(self.data_root):
            data["data-root"] = self.data_root

        if validate(self.debug):
            data["debug"] = self.debug

        if validate(self.default_gateway):
            data["default-gateway"] = self.default_gateway

        if validate(self.default_gateway_v6):
            data["default-gateway-v6"] = self.default_gateway_v6

        if validate(self.default_shm_size):
            data["default-shm-size"] = self.default_shm_size

        if validate(self.default_ulimits):
            data["default-ulimits"] = self.default_ulimits

        if validate(self.dns):
            data["dns"] = self.dns

        if validate(self.dns_opts):
            data["dns-opts"] = self.dns_opts

        if validate(self.dns_search):
            data["dns-search"] = self.dns_search

        if validate(self.experimental):
            data["experimental"] = self.experimental

        if validate(self.fixed_cidr):
            data["fixed-cidr"] = self.fixed_cidr

        if validate(self.fixed_cidr_v6):
            data["fixed-cidr-v6"] = self.fixed_cidr_v6

        if validate(self.group):
            data["group"] = self.group

        if validate(self.hosts):
            data["hosts"] = self.hosts

        if validate(self.insecure_registries):
            data["insecure-registries"] = self.insecure_registries

        if validate(self.ip):
            data["ip"] = self.ip

        if validate(self.ip_forward):
            data["ip-forward"] = self.ip_forward

        if validate(self.ip_masq):
            data["ip-masq"] = self.ip_masq

        if validate(self.iptables):
            data["iptables"] = self.iptables

        if validate(self.ip6tables):
            data["ip6tables"] = self.ip6tables

        if validate(self.ipv6):
            data["ipv6"] = self.ipv6

        if validate(self.labels):
            data["labels"] = self.labels

        if validate(self.log_level) and self.log_level in [
            "debug",
            "info",
            "warn",
            "error",
            "fatal",
        ]:
            data["log-level"] = self.log_level

        if validate(self.log_driver):
            if "loki" in self.log_driver:
                plugin_valid, plugin_state_message = self.__check_plugin()

                if not plugin_valid:
                    self.module.log(msg="ERROR: log_driver are not valid!")
                    self.module.log(msg=f"ERROR: {plugin_state_message}")
                    self.log_driver = "json-file"

            data["log-driver"] = self.log_driver

        if validate(self.log_opts):
            data["log-opts"] = self.__values_as_string(self.log_opts)

        if validate(self.max_concurrent_downloads):
            data["max-concurrent-downloads"] = self.max_concurrent_downloads

        if validate(self.max_concurrent_uploads):
            data["max-concurrent-uploads"] = self.max_concurrent_uploads

        if validate(self.max_download_attempts):
            data["max-download-attempts"] = self.max_download_attempts

        if validate(self.metrics_addr):
            data["metrics-addr"] = self.metrics_addr
            data["experimental"] = True

        if validate(self.oom_score_adjust):
            data["oom-score-adjust"] = self.oom_score_adjust

        if validate(self.pidfile):
            data["pidfile"] = self.pidfile

        if validate(self.raw_logs):
            data["raw-logs"] = self.raw_logs

        if validate(self.registry_mirrors):
            data["registry-mirrors"] = self.registry_mirrors

        if validate(self.seccomp_profile):
            data["seccomp-profile"] = self.seccomp_profile

        if validate(self.selinux_enabled):
            data["selinux-enabled"] = self.selinux_enabled

        if validate(self.shutdown_timeout):
            data["shutdown-timeout"] = self.shutdown_timeout

        if validate(self.storage_driver):
            self.module.log(msg=f"  - {self.storage_driver}")
            self.module.log(msg=f"  - {self.storage_opts}")
            valid_storage_drivers = [
                "aufs",
                "devicemapper",
                "btrfs",
                "zfs",
                "overlay",
                "overlay2",
                "fuse-overlayfs",
            ]
            if self.storage_driver in valid_storage_drivers:
                data["storage-driver"] = self.storage_driver

                if validate(self.storage_opts):
                    """
                    # TODO
                    #  validate storage_opts
                    # -> https://docs.docker.com/engine/reference/commandline/dockerd/#options-per-storage-driver
                    # Options for
                    #   - devicemapper are prefixed with dm
                    #   - zfs start with zfs
                    #   - btrfs start with btrfs
                    #   - overlay2 start with ...
                    """
                    data["storage-opts"] = self.storage_opts

        if self.tls_ca_cert and self.tls_cert and self.tls_key:
            """ """
            data["tls"] = True

            if validate(self.tls_verify):
                data["tlsverify"] = self.tls_verify

            if validate(self.tls_ca_cert):
                data["tlscacert"] = self.tls_ca_cert

            if validate(self.tls_cert):
                data["tlscert"] = self.tls_cert

            if validate(self.tls_key):
                data["tlskey"] = self.tls_key

        return data


def main() -> None:
    """
    Ansible module entry point.

    Defines module arguments, initializes the DockerCommonConfig class,
    and exits with an Ansible-compatible JSON result.
    """
    args = dict(
        state=dict(default="present", choices=["absent", "present"]),
        diff_output=dict(required=False, type="bool", default=False),
        #
        authorization_plugins=dict(required=False, type="list"),
        bip=dict(required=False, type="str"),
        bridge=dict(required=False, type="str"),
        data_root=dict(required=False, type="str"),
        debug=dict(required=False, type="bool", default=False),
        default_gateway=dict(required=False, type="str"),
        default_gateway_v6=dict(required=False, type="str"),
        default_shm_size=dict(required=False, type="str"),
        default_ulimits=dict(required=False, type="dict"),
        dns=dict(required=False, type="list"),
        dns_opts=dict(required=False, type="list"),
        dns_search=dict(required=False, type="list"),
        experimental=dict(required=False, type="bool", default=False),
        fixed_cidr=dict(required=False, type="str"),
        fixed_cidr_v6=dict(required=False, type="str"),
        group=dict(required=False, type="str"),
        hosts=dict(required=False, type="list"),
        insecure_registries=dict(required=False, type="list"),
        ip=dict(required=False, type="str"),
        ip_forward=dict(required=False, type="bool"),
        ip_masq=dict(required=False, type="bool"),
        iptables=dict(required=False, type="bool"),
        ip6tables=dict(required=False, type="bool"),
        ipv6=dict(required=False, type="bool"),
        labels=dict(required=False, type="list"),
        log_driver=dict(required=False, type="str"),
        log_level=dict(required=False, type="str"),
        log_opts=dict(required=False, type="dict"),
        max_concurrent_downloads=dict(required=False, type="int"),
        max_concurrent_uploads=dict(required=False, type="int"),
        max_download_attempts=dict(required=False, type="int"),
        metrics_addr=dict(required=False, type="str"),
        oom_score_adjust=dict(required=False, type="int"),
        pidfile=dict(required=False, type="str"),
        raw_logs=dict(required=False, type="bool"),
        registry_mirrors=dict(required=False, type="list"),
        seccomp_profile=dict(required=False, type="str"),
        selinux_enabled=dict(required=False, type="bool", default=False),
        shutdown_timeout=dict(required=False, type="int"),
        storage_driver=dict(required=False, type="str"),
        storage_opts=dict(required=False, type="list"),
        tls_ca_cert=dict(required=False, type="str"),
        tls_cert=dict(required=False, type="str"),
        tls_key=dict(required=False, type="str"),
        tls_verify=dict(required=False, type="bool", default=False),
    )

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=True,
    )

    handler = DockerCommonConfig(module)
    result = handler.run()

    module.exit_json(**result)


if __name__ == "__main__":
    main()


"""
{
  "allow-nondistributable-artifacts": [],
  "api-cors-header": "",
  "authorization-plugins": [],
  "bip": "",
  "bridge": "",
  "cgroup-parent": "",
  "cluster-advertise": "",
  "cluster-store": "",
  "cluster-store-opts": {},
  "containerd": "/run/containerd/containerd.sock",
  "containerd-namespace": "docker",
  "containerd-plugin-namespace": "docker-plugins",
  "data-root": "",
  "debug": true,
  "default-address-pools": [
    {
      "base": "172.30.0.0/16",
      "size": 24
    },
    {
      "base": "172.31.0.0/16",
      "size": 24
    }
  ],
  "default-cgroupns-mode": "private",
  "default-gateway": "",
  "default-gateway-v6": "",
  "default-runtime": "runc",
  "default-shm-size": "64M",
  "default-ulimits": {
    "nofile": {
      "Hard": 64000,
      "Name": "nofile",
      "Soft": 64000
    }
  },
  "dns": [],
  "dns-opts": [],
  "dns-search": [],
  "exec-opts": [],
  "exec-root": "",
  "experimental": false,
  "features": {},
  "fixed-cidr": "",
  "fixed-cidr-v6": "",
  "group": "",
  "hosts": [],
  "icc": false,
  "init": false,
  "init-path": "/usr/libexec/docker-init",
  "insecure-registries": [],
  "ip": "0.0.0.0",
  "ip-forward": false,
  "ip-masq": false,
  "iptables": false,
  "ip6tables": false,
  "ipv6": false,
  "labels": [],
  "live-restore": true,
  "log-driver": "json-file",
  "log-level": "",
  "log-opts": {
    "cache-disabled": "false",
    "cache-max-file": "5",
    "cache-max-size": "20m",
    "cache-compress": "true",
    "env": "os,customer",
    "labels": "somelabel",
    "max-file": "5",
    "max-size": "10m"
  },
  "max-concurrent-downloads": 3,
  "max-concurrent-uploads": 5,
  "max-download-attempts": 5,
  "mtu": 0,
  "no-new-privileges": false,
  "node-generic-resources": [
    "NVIDIA-GPU=UUID1",
    "NVIDIA-GPU=UUID2"
  ],
  "oom-score-adjust": -500,
  "pidfile": "",
  "raw-logs": false,
  "registry-mirrors": [],
  "runtimes": {
    "cc-runtime": {
      "path": "/usr/bin/cc-runtime"
    },
    "custom": {
      "path": "/usr/local/bin/my-runc-replacement",
      "runtimeArgs": [
        "--debug"
      ]
    }
  },
  "seccomp-profile": "",
  "selinux-enabled": false,
  "shutdown-timeout": 15,
  "storage-driver": "",
  "storage-opts": [],
  "swarm-default-advertise-addr": "",
  "tls": true,
  "tlscacert": "",
  "tlscert": "",
  "tlskey": "",
  "tlsverify": true,
  "userland-proxy": false,
  "userland-proxy-path": "/usr/libexec/docker-proxy",
  "userns-remap": ""
}
"""
