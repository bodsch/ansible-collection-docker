#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2023, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
container_directories.py
========================

An Ansible module that ensures container-specific directories exist under a given base directory.

This module is designed to create one or more directories for containers in a consistent,
idempotent, and permission-controlled way. It verifies existing directory states and
creates missing directories with the specified owner, group, and mode.

Features
--------
- Ensures directories exist for containers (idempotent).
- Applies ownership and permission settings.
- Reports changes in a structured, Ansible-compatible format.
- Uses helper utilities from the bodsch.core collection for consistency.

This module is part of the `bodsch.docker` Ansible collection.
"""

from __future__ import absolute_import, division, print_function

import os
from typing import Any, Dict, List, Optional

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.directory import (
    create_directory,
    current_state,
)
from ansible_collections.bodsch.core.plugins.module_utils.lists import compare_two_lists

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
---
module: container_directories
version_added: "1.0.0"
author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"

short_description: Manage and create container directories.
description:
  - This module ensures that a list of container-specific directories exists under a given base directory.
  - It creates any missing directories and applies the desired owner, group, and permission mode.
  - The module reports whether changes were made and which directories were created or modified.
  - It is designed to be idempotent — no changes will be made if all directories already exist with the correct attributes.

options:
  base_directory:
    description:
      - The base directory under which all container directories will be managed.
      - The module will ensure this directory exists before processing child directories.
    required: true
    type: str

  container:
    description:
      - A list of container directory names or relative paths to be created under C(base_directory).
      - Each entry represents one container directory.
    required: true
    type: list
    elements: str

  owner:
    description:
      - The owner to assign to created directories.
      - If omitted, ownership remains unchanged.
    required: false
    type: str

  group:
    description:
      - The group to assign to created directories.
      - If omitted, group ownership remains unchanged.
    required: false
    type: str

  mode:
    description:
      - The permission mode to apply to created directories, expressed as an octal string (e.g., C(0755)).
      - If omitted, defaults to the system umask.
    required: false
    type: str

notes:
  - The module does not remove any directories.
  - Ownership and permissions are applied only to newly created directories.
  - It uses helper functions from the C(bodsch.core) collection to ensure idempotency and handle filesystem state.
requirements:
  - Python >= 3.6
  - ansible-collection: bodsch.core
"""

EXAMPLES = r"""
# Example 1: Ensure container directories exist with default permissions
- name: Ensure container directories exist
  bodsch.docker.container_directories:
    base_directory: /srv/containers
    container:
      - web
      - db
      - redis

# Example 2: Create directories with specific ownership and permissions
- name: Create container directories with owner and mode
  bodsch.docker.container_directories:
    base_directory: /opt/docker
    container:
      - nginx
      - postgres
    owner: docker
    group: docker
    mode: "0755"

# Example 3: Create nested directories for multiple containers
- name: Create nested container directories
  bodsch.docker.container_directories:
    base_directory: /data/services
    container:
      - app/frontend
      - app/backend
      - monitoring/prometheus
    owner: svcuser
    group: svcgroup
    mode: "0750"

# Example 4: Run in check mode (dry run)
- name: Check directory creation without applying changes
  bodsch.docker.container_directories:
    base_directory: /var/lib/containers
    container:
      - cache
      - logs
  check_mode: true
"""

RETURN = r"""
changed:
  description: Indicates whether any directories were created or modified.
  returned: always
  type: bool
  sample: true

failed:
  description: Whether the module execution failed.
  returned: always
  type: bool
  sample: false

created_directories:
  description:
    - List of directories that were created during module execution.
    - Empty if all directories already existed.
  returned: always
  type: list
  elements: str
  sample:
    - /srv/containers/web
    - /srv/containers/db
    - /srv/containers/redis

msg:
  description:
    - Human-readable status message summarizing module execution.
  returned: always
  type: str
  sample: "3 directories created under /srv/containers."
"""

# ---------------------------------------------------------------------------------------


class ContainerDirectories:
    """
    Manage and ensure container directories exist under a specified base directory.

    This class provides logic to verify and create directories for containers
    based on the parameters provided via the Ansible module.

    The directories can be created with specific ownership and permission modes.
    If directories already exist with the desired attributes, no changes are made.

    Attributes:
        module (AnsibleModule): The Ansible module instance managing execution.
        base_directory (str): The base directory path under which container directories are managed.
        container (List[str]): List of container directories or relative paths to manage.
        owner (Optional[str]): The owner to assign to created directories.
        group (Optional[str]): The group to assign to created directories.
        mode (Optional[str]): The permission mode (octal string, e.g., '0755') for directories.
    """

    module: AnsibleModule
    base_directory: str
    container: List[Dict[str, Any]]
    owner: Optional[str]
    group: Optional[str]
    mode: Optional[str]

    def __init__(self, module: AnsibleModule) -> None:
        """
        Initialize the ContainerDirectories handler.

        Args:
            module (AnsibleModule): The active Ansible module instance.

        This constructor retrieves parameters from the Ansible context and prepares
        the module for directory management operations.
        """
        self.module = module

        # Retrieve and typecast module arguments safely
        self.base_directory = str(module.params.get("base_directory"))
        self.container = list(module.params.get("container", []))
        self.owner = module.params.get("owner")
        self.group = module.params.get("group")
        self.mode = module.params.get("mode")

    def run(self) -> Dict[str, Any]:
        """
        Execute the main module logic.

        Iterates through the list of container directories, checks their existence,
        creates them if necessary, and records any changes made.

        Returns:
            dict: A result dictionary compatible with Ansible, containing:
                - changed (bool): Whether any directories were created or modified.
                - failed (bool): Whether the module execution failed.
                - created_directories (List[str]): List of directories that were created.
        """
        result: Dict[str, Any] = {"changed": False, "failed": True, "msg": "initial"}
        created_directories: List[str] = []
        changed: bool = False

        # Ensure base directory exists
        if not os.path.isdir(self.base_directory):
            create_directory(directory=self.base_directory, mode="0755")

        # Process each container directory
        for directory in self.container:
            d: str = os.path.join(self.base_directory, directory)
            self.module.log(f" - directory: {d}")

            if not os.path.isdir(d):
                pre: List[Dict[str, Dict[str, str]]] = self.__analyse_directory(d)
                create_directory(
                    directory=d, owner=self.owner, group=self.group, mode=self.mode
                )
                post: List[Dict[str, Dict[str, str]]] = self.__analyse_directory(d)

                changed_dir, diff, _ = compare_two_lists(pre, post)
                self.module.log(f"   changed: {changed_dir}, diff: {diff}")

                if changed_dir:
                    created_directories.append(d)
                    changed = True

        result.update(
            {
                "changed": changed,
                "failed": False,
                "created_directories": created_directories,
            }
        )

        return result

    def __analyse_directory(self, directory: str) -> List[Dict[str, Dict[str, str]]]:
        """
        Inspect the current state of a directory (owner, group, mode).

        Args:
            directory (str): The path to the directory to analyze.

        Returns:
            List[Dict[str, Dict[str, str]]]:
                A list containing one dictionary with directory attributes:
                - owner
                - group
                - mode
        """
        result: List[Dict[str, Dict[str, str]]] = []
        res: Dict[str, Dict[str, str]] = {directory: {}}

        current_owner, current_group, current_mode = current_state(directory)
        res[directory].update(
            {
                "owner": current_owner,
                "group": current_group,
                "mode": current_mode,
            }
        )

        result.append(res)
        return result


# ---------------------------------------------------------------------------------------


def main() -> None:
    """
    Entry point for the Ansible module.

    Defines module arguments, initializes the module, and executes it.
    """
    args: Dict[str, Dict[str, Any]] = {
        "base_directory": {"required": True, "type": "str"},
        "container": {"required": True, "type": "list"},
        "owner": {"required": False, "type": "str"},
        "group": {"required": False, "type": "str"},
        "mode": {"required": False, "type": "str"},
    }

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=True,
    )

    handler: ContainerDirectories = ContainerDirectories(module)
    result: Dict[str, Any] = handler.run()

    module.log(msg=f"= result: {result}")
    module.exit_json(**result)


if __name__ == "__main__":
    main()
