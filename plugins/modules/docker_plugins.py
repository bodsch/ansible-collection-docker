#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2023, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
docker_plugins.py
=================

An Ansible module for managing Docker plugins.

This module allows installation, upgrade, or removal of Docker plugins
using the Docker SDK for Python. It provides detailed plugin state
inspection and ensures idempotent behavior by comparing installed versions.

Features:
---------
- Install or remove Docker plugins.
- Detect existing plugin state and version.
- Automatically enable and reload plugins after installation.
- Supports "test" mode for dry-run inspection without modification.

This module is part of the `bodsch.docker` Ansible collection.
"""

from __future__ import absolute_import, division, print_function

import json
import os
from typing import Any, Dict, Optional, Tuple

import docker
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.directory import (
    create_directory,
)

__metaclass__ = type

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
---
module: docker_plugins
author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
version_added: "1.0.0"

short_description: Manage Docker plugins.
description:
  - This module manages Docker plugins through the Docker Engine API.
  - It can install, update, or remove plugins and provides detailed status information.
  - The module uses the Docker SDK for Python and supports dry-run testing.

options:
  state:
    description:
      - Desired state of the plugin.
      - C(present) installs or updates the plugin.
      - C(absent) removes the plugin.
      - C(test) performs a dry-run without making any changes.
    type: str
    choices: ["absent", "present", "test"]
    default: "present"

  plugin_source:
    description:
      - The source image name from which the plugin is installed.
      - Typically corresponds to a Docker Hub plugin name or local registry path.
    required: true
    type: str

  plugin_version:
    description:
      - The desired plugin version to install.
      - Defaults to C(latest) if unspecified.
    required: false
    type: str
    default: "latest"

  plugin_alias:
    description:
      - Local alias for the plugin.
      - Used as the name reference when enabling, disabling, or removing the plugin.
    required: true
    type: str

  data_root:
    description:
      - The Docker data root directory where plugins are stored.
      - Used to validate installed plugin paths.
    required: false
    type: str
    default: "/var/lib/docker"

notes:
  - This module requires the Docker SDK for Python (C(pip install docker)).
  - It interacts directly with the Docker daemon and requires appropriate permissions.
  - A cache directory is created under C(/var/cache/ansible/docker) for plugin state storage.

requirements:
  - Python >= 3.6
  - docker >= 4.0.0
"""

EXAMPLES = r"""
# Example 1: Install a Docker plugin
- name: Install a Docker logging plugin
  bodsch.docker.docker_plugins:
    state: present
    plugin_source: grafana/loki-docker-driver
    plugin_version: latest
    plugin_alias: loki
    data_root: /var/lib/docker

# Example 2: Remove a Docker plugin
- name: Uninstall an existing plugin
  bodsch.docker.docker_plugins:
    state: absent
    plugin_source: grafana/loki-docker-driver
    plugin_alias: loki

# Example 3: Dry-run test for plugin state
- name: Check plugin installation without changes
  bodsch.docker.docker_plugins:
    state: test
    plugin_source: grafana/loki-docker-driver
    plugin_alias: loki
"""

RETURN = r"""
changed:
  description: Whether the plugin was installed, removed, or modified.
  type: bool
  returned: always
  sample: true

failed:
  description: Indicates if an error occurred during the operation.
  type: bool
  returned: always
  sample: false

installed:
  description: Whether the plugin is currently installed.
  type: bool
  returned: when state=test
  sample: true

equal_versions:
  description: Whether the installed plugin version matches the desired version.
  type: bool
  returned: when state=test
  sample: false

msg:
  description: Human-readable summary of the module's result.
  type: str
  returned: always
  sample: "plugin loki was successfully installed in version 2.9.3"
"""

# ---------------------------------------------------------------------------------------


class DockerPlugins:
    """
    Ansible helper class to manage Docker plugin installation and removal.

    This class encapsulates Docker plugin operations using the Docker SDK,
    including checking plugin state, installing or removing plugins, and
    writing cached plugin information for future validation.

    Attributes:
        module (AnsibleModule): The active Ansible module instance.
        state (str): Desired plugin state ('present', 'absent', 'test').
        plugin_source (str): Source image for plugin installation.
        plugin_version (str): Desired version of the plugin.
        plugin_alias (str): Local alias of the plugin.
        docker_data_root (str): Docker data directory for validation.
        cache_directory (str): Directory for storing plugin metadata.
        plugin_information_file (str): File path for cached plugin information.
        docker_socket (str): Path to the Docker daemon socket.
    """

    module = None

    def __init__(self, module: AnsibleModule) -> None:
        """Initialize module parameters and Docker connection settings."""
        self.module = module
        self.state = module.params.get("state")
        self.plugin_source = module.params.get("plugin_source")
        self.plugin_version = module.params.get("plugin_version")
        self.plugin_alias = module.params.get("plugin_alias")
        self.docker_data_root = module.params.get("data_root")

        self.cache_directory = "/var/cache/ansible/docker"
        self.plugin_information_file = os.path.join(
            self.cache_directory, f"plugin_{self.plugin_alias}"
        )
        self.docker_socket = "/var/run/docker.sock"
        self.docker_client = None
        self.installed_plugin_data: Dict[str, Any] = {}

    def run(self) -> Dict[str, Any]:
        """
        Execute the main module logic for Docker plugin management.

        Returns:
            dict: Ansible result dictionary with keys:
                - changed (bool)
                - failed (bool)
                - msg (str)
        """
        try:
            if os.path.exists(self.docker_socket):
                self.docker_client = docker.DockerClient(
                    base_url=f"unix://{self.docker_socket}"
                )
            else:
                self.docker_client = docker.from_env()

            if not self.docker_client.ping():
                return dict(
                    changed=False, failed=True, msg="Docker daemon is not reachable"
                )

        except docker.errors.DockerException as e:
            return dict(changed=False, failed=True, msg=f"Docker connection error: {e}")

        create_directory(self.cache_directory)

        plugin_state, plugin_id, version_equal, msg = self.check_plugin()
        self.module.log(msg=f"Plugin check result: {msg}")

        if self.state == "test":
            return dict(
                changed=False,
                installed=plugin_state,
                equal_versions=version_equal,
                msg=msg,
            )

        if self.state == "absent":
            return self.uninstall_plugin()

        return self.install_plugin()

    def check_plugin(self) -> Tuple[bool, Optional[str], bool, str]:
        """
        Check if the desired plugin is already installed.

        Returns:
            tuple: (installed, plugin_id, equal_version, message)
        """
        try:
            plugins = self.docker_client.plugins.list()
        except docker.errors.APIError as e:
            return False, None, False, f"Docker API error: {e}"

        for plugin in plugins:
            short_name = plugin.name.split(":")[0]
            version = plugin.name.split(":")[1] if ":" in plugin.name else None

            if short_name == self.plugin_alias:
                self.installed_plugin_data = dict(
                    id=plugin.id,
                    short_id=plugin.short_id,
                    name=plugin.name,
                    version=version,
                    enabled=plugin.enabled,
                )
                if version == self.plugin_version:
                    self._write_plugin_information(self.installed_plugin_data)
                    return (
                        True,
                        plugin.id,
                        True,
                        f"Plugin {short_name} already installed in version {version}",
                    )

                return (
                    True,
                    plugin.id,
                    False,
                    f"Plugin {short_name} installed with different version ({version})",
                )

        return False, None, False, f"Plugin {self.plugin_alias} not installed"

    def install_plugin(self) -> Dict[str, Any]:
        """Install or re-enable a Docker plugin."""
        try:
            plugin = self.docker_client.plugins.get(
                f"{self.plugin_alias}:{self.plugin_version}"
            )
            self.module.log(msg=f"Plugin {self.plugin_alias} found, re-enabling...")
        except docker.errors.APIError:
            plugin = None

        if plugin:
            try:
                plugin.enable(timeout=10)
                plugin.reload()
                return dict(
                    changed=True,
                    failed=False,
                    msg=f"Plugin {self.plugin_alias} re-enabled.",
                )
            except docker.errors.APIError as e:
                return dict(
                    changed=False, failed=True, msg=f"Failed to enable plugin: {e}"
                )

        try:
            self.module.log(
                msg=f"Installing plugin {self.plugin_source}:{self.plugin_version}"
            )
            plugin = self.docker_client.plugins.install(
                remote_name=f"{self.plugin_source}:{self.plugin_version}",
                local_name=f"{self.plugin_alias}:{self.plugin_version}",
            )
            plugin.enable(timeout=10)
            plugin.reload()

            return dict(
                changed=True,
                failed=False,
                msg=f"Plugin {self.plugin_alias} successfully installed in version {self.plugin_version}",
            )
        except docker.errors.APIError as e:
            return dict(
                changed=False, failed=True, msg=f"Plugin installation failed: {e}"
            )

    def uninstall_plugin(self) -> Dict[str, Any]:
        """Remove a Docker plugin if it exists."""
        plugin_name = self.installed_plugin_data.get("name", None)
        if not plugin_name:
            return dict(changed=False, failed=False, msg="Plugin is not installed.")

        try:
            plugin = self.docker_client.plugins.get(plugin_name)
            plugin.disable(force=True)
            plugin.remove(force=True)
            self._remove_plugin_information()
            return dict(
                changed=True,
                failed=False,
                msg=f"Plugin {plugin_name} successfully removed.",
            )
        except docker.errors.APIError as e:
            return dict(changed=False, failed=True, msg=f"Failed to remove plugin: {e}")

    def _write_plugin_information(self, data: Dict[str, Any]) -> None:
        """Persist plugin information locally."""
        create_directory(self.cache_directory)
        with open(self.plugin_information_file, "w") as fp:
            json.dump(data, fp, indent=2)

    def _remove_plugin_information(self) -> None:
        """Delete the stored plugin information file if present."""
        if os.path.exists(self.plugin_information_file):
            os.remove(self.plugin_information_file)


def main() -> None:
    """Main entry point for the Ansible module."""

    args = dict(
        state=dict(default="present", choices=["absent", "present", "test"]),
        #
        plugin_source=dict(required=True, type="str"),
        plugin_version=dict(required=False, type="str", default="latest"),
        plugin_alias=dict(required=True, type="str"),
        data_root=dict(type="str", default="/var/lib/docker"),
    )

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=True,
    )

    handler = DockerPlugins(module)
    result = handler.run()

    module.log(msg=f"= result: {result}")
    module.exit_json(**result)


# import module snippets
if __name__ == "__main__":
    main()
