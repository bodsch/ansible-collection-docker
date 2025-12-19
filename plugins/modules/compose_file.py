#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2023, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
compose_file.py
===============

An Ansible module for managing Docker Compose YAML files.

This module allows you to create, update, and remove Docker Compose files
on a managed system. It supports change detection through file checksums
and automatic directory creation.

Features:
---------
- Create or update Docker Compose files from structured Ansible data.
- Remove existing Compose files when no longer needed.
- Detect changes to avoid unnecessary writes.
- Work safely with temporary directories for atomic file operations.

This module is part of the `bodsch.docker` Ansible collection.
"""

from __future__ import absolute_import, division, print_function

import os
import shutil
from typing import Any, Dict

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.directory import (
    create_directory,
)
from ansible_collections.bodsch.docker.plugins.module_utils.compose_file import (
    ComposeFile,
)

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
---
module: compose_file
author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
version_added: "1.0.0"

short_description: Manage Docker Compose YAML files
description:
  - This module creates, updates, or removes Docker Compose files on a target system.
  - It supports automatic directory creation, file validation, and change detection.
  - The module is useful for generating Compose files dynamically based on structured Ansible data.

options:
  state:
    description:
      - Desired state of the Docker Compose file.
      - When C(present), the compose file is created or updated.
      - When C(absent), the compose file is deleted.
      - When C(test), no action is performed (used for dry-run or testing logic).
    required: false
    type: str
    choices: ["present", "absent", "test"]
    default: present

  base_directory:
    description:
      - Directory where the Docker Compose file will be placed.
      - If the directory does not exist, it will be created automatically.
    required: true
    type: str

  name:
    description:
      - The filename of the Docker Compose file (e.g., C(docker-compose.yml)).
    required: true
    type: str

  networks:
    description:
      - Dictionary defining the networks section in the Docker Compose file.
      - Matches the YAML structure of the C(networks) key in Compose.
    required: false
    type: dict

  services:
    description:
      - Dictionary defining the services section of the Docker Compose file.
      - Each service entry should match the Docker Compose YAML specification.
    required: false
    type: dict

  volumes:
    description:
      - Dictionary defining the volumes section in the Docker Compose file.
    required: false
    type: dict

notes:
  - This module does not execute C(docker-compose) commands.
  - It only manages the Docker Compose YAML file on disk.
  - File comparison and validation are handled internally using the ComposeFile helper.
requirements:
  - Python >= 3.6
  - Ansible >= 2.10
"""

EXAMPLES = r"""
# Create a Docker Compose file
- name: Create docker-compose.yml for an application
  bodsch.docker.compose_file:
    state: present
    base_directory: /opt/myapp
    name: docker-compose.yml
    networks:
      frontend:
        driver: bridge
    services:
      web:
        image: nginx:latest
        ports:
          - "80:80"
        networks:
          - frontend
      app:
        image: myapp:latest
        depends_on:
          - web
        networks:
          - frontend
    volumes:
      data:
        driver: local
  register: compose_result

- name: "compose #1"
  bodsch.docker.compose_file:
    base_directory: "/tmp/docker-compose.d"
    name: compose.yml
    state: present
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

- name: Remove docker-compose.yml
  bodsch.docker.compose_file:
    state: absent
    base_directory: /opt/myapp
    name: docker-compose.yml

- name: Test compose file generation (no changes applied)
  bodsch.docker.compose_file:
    state: test
    base_directory: /opt/myapp
    name: docker-compose.yml
"""

RETURN = r"""
changed:
  description: Indicates if the compose file was created, modified, or removed.
  type: bool
  returned: always
  sample: true

failed:
  description: Indicates if the module execution failed.
  type: bool
  returned: always
  sample: false

msg:
  description: Descriptive message about the performed action.
  type: str
  returned: always
  sample: "The compose file ‘docker-compose.yml’ was successfully written."
"""

# ---------------------------------------------------------------------------------------


class ModuleComposeFile:
    """
    Ansible helper class to manage Docker Compose YAML files.

    This class provides the logic for:
      - Creating or updating Docker Compose files.
      - Deleting existing Compose files.
      - Validating changes based on checksum comparison.

    Attributes:
        module (AnsibleModule): The active Ansible module object.
        state (str): Desired state of the file ('present', 'absent', or 'test').
        base_directory (str): Target directory for the Compose file.
        compose_filename (str): Name of the Compose file.
        networks (dict): Network definitions for the Compose file.
        services (dict): Service definitions for the Compose file.
        volumes (dict): Volume definitions for the Compose file.
        tmp_directory (str): Temporary directory used for safe file writes.
    """

    def __init__(self, module: AnsibleModule) -> None:
        """
        Initialize the module and read parameters from Ansible.

        Args:
            module (AnsibleModule): The Ansible module instance.
        """
        self.module = module
        self.state: str = module.params.get("state")

        self.base_directory: str = module.params.get("base_directory")
        self.compose_filename: str = module.params.get("name")
        self.networks: Dict[str, Any] = module.params.get("networks")
        self.services: Dict[str, Any] = module.params.get("services")
        self.volumes: Dict[str, Any] = module.params.get("volumes")

        pid = os.getpid()
        self.tmp_directory: str = os.path.join(
            "/run/.ansible", f"compose_file.{str(pid)}"
        )

    def run(self) -> Dict[str, Any]:
        """
        Execute the main module logic.

        Returns:
            dict: Ansible result dictionary containing:
                - changed (bool): Whether the file was created, modified, or deleted.
                - failed (bool): Whether the operation failed.
                - msg (str): A descriptive message of the action performed.
        """
        result = dict(changed=False, failed=True, msg="initial")

        file_name = os.path.join(self.base_directory, self.compose_filename)

        if self.state == "absent":
            return self._remove_file(file_name)

        if self.state == "present":
            return self._create_or_update_file(file_name)

        if self.state == "test":
            result["msg"] = "Test mode - no changes applied."
            return result

        self.module.fail_json(msg=f"Unsupported state: {self.state}")

        return result  # Unreachable, added for type-checking completeness

        # if self.state == "absent":
        #     if os.path.exists(file_name):
        #         _msg = f"The compose file ‘{self.compose_filename}’ was successfully deleted."
        #         _changed = True
        #         os.remove(file_name)
        #     else:
        #         _msg = f"The compose file ‘{self.compose_filename}’ has already been deleted."
        #         _changed = False
        #
        #     return dict(changed=_changed, failed=False, msg=_msg)
        #
        # if self.state == "present":
        #     create_directory(directory=self.tmp_directory, mode="0750")
        #
        #     if not os.path.isdir(self.base_directory):
        #         create_directory(directory=self.base_directory, mode="0755")
        #
        #     self.composeFile = ComposeFile(self.module)
        #
        #     compose_data = self.composeFile.create(
        #         networks=self.networks,
        #         services=self.services,
        #         volumes=self.volumes
        #     )
        #
        #     tmp_file_name = os.path.join(self.tmp_directory, self.compose_filename)
        #
        #     self.composeFile.write(tmp_file_name, compose_data)
        #     _changed = self.composeFile.validate(tmp_file_name, file_name)
        #
        #     if _changed:
        #         shutil.move(tmp_file_name, file_name)
        #         _msg = f"The compose file ‘{self.compose_filename}’ was successful written."
        #     else:
        #         _msg = (
        #             f"The compose file ‘{self.compose_filename}’ has not been changed."
        #         )
        #
        #     shutil.rmtree(self.tmp_directory)
        #
        #     return dict(changed=_changed, failed=False, msg=_msg)
        #
        # if self.state == "test":
        #     return result

    def _remove_file(self, file_path: str) -> Dict[str, Any]:
        """
        Remove the existing Compose file, if it exists.

        Args:
            file_path (str): Path to the file to remove.

        Returns:
            dict: Ansible result dictionary.
        """
        if os.path.exists(file_path):
            os.remove(file_path)
            return dict(
                changed=True,
                failed=False,
                msg=f"The compose file '{self.compose_filename}' was successfully deleted.",
            )

        return dict(
            changed=False,
            failed=False,
            msg=f"The compose file '{self.compose_filename}' has already been deleted.",
        )

    def _create_or_update_file(self, file_path: str) -> Dict[str, Any]:
        """
        Create or update the Docker Compose file.

        This method:
          - Ensures the target and temporary directories exist.
          - Builds the Compose file structure using the ComposeFile helper.
          - Writes a temporary file and compares it with the existing one.
          - Replaces the old file only if content has changed.

        Args:
            file_path (str): Destination path for the Compose file.

        Returns:
            dict: Ansible result dictionary.
        """
        try:
            create_directory(directory=self.tmp_directory, mode="0750")

            if not os.path.isdir(self.base_directory):
                create_directory(directory=self.base_directory, mode="0755")

            compose_file = ComposeFile(self.module)
            compose_data = compose_file.create(
                networks=self.networks,
                services=self.services,
                volumes=self.volumes,
            )

            tmp_file_path = os.path.join(self.tmp_directory, self.compose_filename)
            compose_file.write(tmp_file_path, compose_data)
            changed = compose_file.validate(tmp_file_path, file_path)

            if changed:
                shutil.move(tmp_file_path, file_path)
                msg = f"The compose file '{self.compose_filename}' was successfully written."
            else:
                msg = (
                    f"The compose file '{self.compose_filename}' has not been changed."
                )

            shutil.rmtree(self.tmp_directory)

            return dict(changed=changed, failed=False, msg=msg)

        except Exception as e:
            self.module.fail_json(msg=f"Error managing compose file: {e}")
            return dict(
                changed=False, failed=True, msg=str(e)
            )  # fallback for static analyzers


# ---------------------------------------------------------------------------------------


def main():
    """
    Entry point for the Ansible module.

    Defines module arguments, initializes the module, and executes it.
    """
    args = dict(
        state=dict(default="present", choices=["absent", "present", "test"]),
        base_directory=dict(required=True, type="str"),
        name=dict(required=True, type="str"),
        networks=dict(required=False, type="dict", default={}),
        services=dict(required=False, type="dict", default={}),
        volumes=dict(required=False, type="dict", default={}),
    )

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=True,
    )

    handler = ModuleComposeFile(module)
    result = handler.run()

    module.log(msg=f"= result: {result}")
    module.exit_json(**result)


if __name__ == "__main__":
    main()
