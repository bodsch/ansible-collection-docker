#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2023, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
compose_files.py
================

An Ansible module for managing multiple Docker Compose fragment files.

This module allows you to generate individual `.conf` files for
Docker Compose networks, services, and volumes based on structured
Ansible data.

Each Compose fragment can be created, updated, or deleted independently,
making this module suitable for modular Docker Compose configurations.

Features:
---------
- Manage multiple Docker Compose YAML fragments.
- Create, update, or remove network/service/volume configurations.
- Automatically detects content changes using checksums.
- Cleans up temporary directories after processing.

This module is part of the `bodsch.docker` Ansible collection.
"""

from __future__ import absolute_import, division, print_function

import os
import shutil
from typing import Any, Dict, List

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.directory import (
    create_directory,
)
from ansible_collections.bodsch.core.plugins.module_utils.module_results import results
from ansible_collections.bodsch.docker.plugins.module_utils.compose_file import (
    ComposeFile,
)

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
---
module: compose_files
author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
version_added: "1.0.0"

short_description: Manage multiple Docker Compose fragment files.
description:
  - This module manages multiple Docker Compose fragment files for networks, services, and volumes.
  - It allows creating, updating, and deleting individual Compose fragments stored as C(.conf) files.
  - Each fragment represents a portion of a Docker Compose configuration, making it ideal for modular setups.
  - The module automatically detects configuration changes and only updates files when necessary.

options:
  base_directory:
    description:
      - The target directory where all Docker Compose fragment files will be stored.
      - Each fragment will be saved as a C(.conf) file under this directory.
    required: true
    type: str

  networks:
    description:
      - A list of network configuration dictionaries to be managed.
      - Each item must contain at least a C(name) key.
      - Each entry can also include a C(state) key to control whether the fragment is present or absent.
    required: false
    type: list
    elements: dict
    suboptions:
      name:
        description: The name of the Docker network.
        required: true
        type: str
      state:
        description:
          - Desired state of the network fragment.
          - Use C(present) to create/update and C(absent) to delete the file.
        type: str
        choices: ["present", "absent"]
        default: present

  services:
    description:
      - A list of Docker service definitions to be managed as Compose fragments.
      - Each item represents a single service stored as an independent Compose C(.conf) file.
    required: false
    type: list
    elements: dict
    suboptions:
      name:
        description: The name of the Docker service.
        required: true
        type: str
      state:
        description:
          - Desired state of the service fragment.
          - Use C(present) to create/update and C(absent) to delete the file.
        type: str
        choices: ["present", "absent"]
        default: present

  volumes:
    description:
      - A list of Docker volume definitions to be managed as Compose fragments.
      - Each item represents a single volume stored as a Compose C(.conf) file.
    required: false
    type: list
    elements: dict
    suboptions:
      name:
        description: The name of the Docker volume.
        required: true
        type: str
      state:
        description:
          - Desired state of the volume fragment.
          - Use C(present) to create/update and C(absent) to delete the file.
        type: str
        choices: ["present", "absent"]
        default: present

notes:
  - The module only manages Compose YAML fragments; it does not execute C(docker-compose).
  - Change detection is checksum-based, ensuring idempotent behavior.
  - A temporary working directory under C(/run/.ansible) is used for safe file operations.

requirements:
  - Python >= 3.6
  - Ansible >= 2.10
  - bodsch.core and bodsch.docker Ansible Collections
"""

EXAMPLES = r"""
# Example 1: Create network, service, and volume fragments
- name: Create Docker Compose fragments
  bodsch.docker.compose_files:
    base_directory: "/etc/docker/compose.d"
    networks:
      - name: frontend
        state: present
        driver: bridge
    services:
      - name: web
        state: present
        image: nginx:latest
        restart: unless-stopped
        ports:
          - "80:80"
        networks:
          - frontend
    volumes:
      - name: web_data
        state: present

# Example 2: Remove an existing service fragment
- name: Remove service configuration
  bodsch.docker.compose_files:
    base_directory: "/etc/docker/compose.d"
    services:
      - name: web
        state: absent

# Example 3: Manage multiple Compose fragments with different states
- name: Manage multiple Docker Compose entities
  bodsch.docker.compose_files:
    base_directory: "/opt/compose.d"
    networks:
      - name: mailcow
        state: present
        driver: bridge
        enable_ipv6: false
        ipam:
          driver: default
          config:
            - subnet: "172.22.1.0/24"
    services:
      - name: memcached
        state: absent
        image: memcached:alpine
        restart: unless-stopped
        environment:
          - TZ=Europe/Berlin
    volumes:
      - name: vmail-vol-1
        state: present
      - name: vmail-index-vol-1
        state: present
"""

RETURN = r"""
changed:
  description: Indicates if any Compose fragment file was created, modified, or deleted.
  type: bool
  returned: always
  sample: true

failed:
  description: Indicates if the operation failed.
  type: bool
  returned: always
  sample: false

networks:
  description: Detailed results for managed Docker network fragments.
  type: dict
  returned: always
  sample:
    changed: true
    failed: false
    msg:
      - mailcow:
          changed: true
          msg: "The compose file 'mailcow.conf' was successfully written."

services:
  description: Detailed results for managed Docker service fragments.
  type: dict
  returned: always
  sample:
    changed: false
    failed: false
    msg:
      - web:
          changed: false
          msg: "The compose file 'web.conf' has not been changed."

volumes:
  description: Detailed results for managed Docker volume fragments.
  type: dict
  returned: always
  sample:
    changed: true
    failed: false
    msg:
      - vmail-vol-1:
          changed: true
          msg: "The compose file 'vmail-vol-1.conf' was successfully written."
"""

# ---------------------------------------------------------------------------------------


class ModuleComposeFiles(object):
    """
    Manage multiple Docker Compose fragment files (networks, services, volumes).

    This class provides the logic for generating and maintaining multiple
    Docker Compose `.conf` fragments. Each fragment represents a portion of
    a Docker Compose configuration (e.g., a single service or network).

    Attributes:
        module (AnsibleModule): The current Ansible module instance.
        base_directory (str): The base directory for storing Compose fragment files.
        networks (list): List of network definitions with states.
        services (list): List of service definitions with states.
        volumes (list): List of volume definitions with states.
        tmp_directory (str): Temporary directory for safe write operations.
    """

    def __init__(self, module: AnsibleModule) -> None:
        """
        Initialize the Compose file handler with module parameters.

        Args:
            module (AnsibleModule): The Ansible module instance.
        """
        self.module = module

        self.base_directory: str = module.params.get("base_directory")
        # self.compose_filename = module.params.get("name")
        self.networks: List[Dict[str, Any]] = module.params.get("networks", [])
        self.services: List[Dict[str, Any]] = module.params.get("services", [])
        self.volumes: List[Dict[str, Any]] = module.params.get("volumes", [])

        pid = os.getpid()

        self.tmp_directory: str = os.path.join(
            "/run/.ansible", f"compose_files.{str(pid)}"
        )

    def run(self) -> Dict[str, Any]:
        """
        Execute the main module logic.

        Returns:
            dict: Ansible-compatible result dictionary containing:
                - changed (bool): Whether any files were changed.
                - failed (bool): Whether an error occurred.
                - networks (dict): Results for network fragments.
                - services (dict): Results for service fragments.
                - volumes (dict): Results for volume fragments.
        """
        create_directory(directory=self.tmp_directory, mode="0750")

        if not os.path.isdir(self.base_directory):
            create_directory(directory=self.base_directory, mode="0755")

        self.composeFile = ComposeFile(self.module)

        network_result = self._save_networks()
        service_result = self._save_services()
        volume_result = self._save_volumes()

        changed = (
            network_result.get("changed", False)
            or service_result.get("changed", False)
            or volume_result.get("changed", False)
        )

        shutil.rmtree(self.tmp_directory)

        return dict(
            changed=changed,
            failed=False,
            networks=network_result,
            services=service_result,
            volumes=volume_result,
        )

    # -------------------------------------------------------------------------
    # Helper functions
    # -------------------------------------------------------------------------

    def _save_networks(self) -> Dict[str, Any]:
        """
        Create or remove Compose files for networks.

        Returns:
            dict: Summary result for all network operations.
        """
        return self._save_entities(self.networks, "networks")

    def _save_services(self) -> Dict[str, Any]:
        """
        Create or remove Compose files for services.

        Returns:
            dict: Summary result for all service operations.
        """
        return self._save_entities(self.services, "services")

    def _save_volumes(self) -> Dict[str, Any]:
        """
        Create or remove Compose files for volumes.

        Returns:
            dict: Summary result for all volume operations.
        """
        return self._save_entities(self.volumes, "volumes")

    def _save_entities(
        self, entities: List[Dict[str, Any]], entity_type: str
    ) -> Dict[str, Any]:
        """
        Generic helper for processing network, service, or volume entries.

        Args:
            entities (list): List of entity dictionaries (e.g., services).
            entity_type (str): One of "services", "networks", or "volumes".

        Returns:
            dict: Combined Ansible result for the given entity type.
        """
        result_state = []

        for entity in entities:
            name = entity.get("name")
            state = entity.get("state", "present")

            if not name:
                continue

            file_name = os.path.join(self.base_directory, f"{name}.conf")

            if state == "absent":
                entity_res = {name: self.__file_state_absent(name, file_name)}

            else:
                # remove redundant keys
                entity = {k: v for k, v in entity.items() if k not in ("name", "state")}
                data = {name: entity}
                entity_res = {
                    name: self.__file_state_present(
                        entity_name=name,
                        file_name=file_name,
                        compose_type=entity_type,
                        data=data,
                    )
                }

            result_state.append(entity_res)

        _, changed, failed, *_ = results(self.module, result_state)
        return dict(changed=changed, failed=failed, msg=result_state)

    # -------------------------------------------------------------------------
    # File state handling
    # -------------------------------------------------------------------------

    def __file_state_absent(self, name: str, file_name: str) -> Dict[str, Any]:
        """
        Delete a Compose fragment file if it exists.

        Args:
            name (str): Name of the entity (e.g., service or network).
            file_name (str): Path to the Compose file to remove.

        Returns:
            dict: Result containing change state and message.
        """
        if os.path.exists(file_name):
            os.remove(file_name)
            msg = f"The compose file ‘{name}.conf’ was successfully deleted."
            changed = True
        else:
            msg = f"The compose file ‘{name}.conf’ has already been deleted."
            changed = False

        return dict(changed=changed, failed=False, msg=msg)

    def __file_state_present(
        self,
        entity_name: str,
        file_name: str,
        compose_type: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create or update a Compose fragment file if the data has changed.

        Args:
            entity_name (str): Name of the entity (e.g., service or network).
            file_name (str): Target Compose file path.
            compose_type (str): Type of compose fragment ("services", "networks", "volumes").
            data (dict): YAML structure to write.

        Returns:
            dict: Result containing change state and message.
        """
        compose_data = self.composeFile.create(**{compose_type: data})

        tmp_file_name = os.path.join(self.tmp_directory, f"{entity_name}.conf")
        self.composeFile.write(tmp_file_name, compose_data)

        changed = self.composeFile.validate(tmp_file_name, file_name)

        if changed:
            shutil.move(tmp_file_name, file_name)
            msg = f"The compose file '{entity_name}.conf' was successfully written."
        else:
            msg = f"The compose file '{entity_name}.conf' has not been changed."

        return dict(changed=changed, failed=False, msg=msg)


# ---------------------------------------------------------------------------------------


def main():
    """ """
    args = dict(
        base_directory=dict(required=True, type="str"),
        networks=dict(required=False, type="list", default=[]),
        services=dict(required=False, type="list", default=[]),
        volumes=dict(required=False, type="list", default=[]),
    )

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=True,
    )

    handler = ModuleComposeFiles(module)
    result = handler.run()

    module.log(msg=f"= result: {result}")
    module.exit_json(**result)


if __name__ == "__main__":
    main()
