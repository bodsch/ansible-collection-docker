#!/usr/bin/python3
# -*- coding: utf-8 -*-
# (c) 2023-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

"""
Utility class for creating, writing, and validating Docker Compose YAML files.
"""

from __future__ import absolute_import, division, print_function

import os
from typing import Any, Dict, Optional

import ruamel.yaml
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.checksum import Checksum


class ComposeFile:
    """
    Helper class to create, write, and validate Docker Compose YAML configurations.
    """

    def __init__(self, module: AnsibleModule) -> None:
        """
        Initialize the ComposeFile helper.

        Args:
            module: AnsibleModule instance for logging and error handling.
        """
        self.module = module
        self.yaml = ruamel.yaml.YAML()
        self.yaml.indent(sequence=4, offset=2)

    def create(
        self,
        version: Optional[str] = None,
        networks: Optional[Dict[str, Any]] = None,
        services: Optional[Dict[str, Any]] = None,
        volumes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build a Docker Compose file dictionary.

        Args:
            version: Compose file schema version (e.g. '3.9').
            networks: Optional network definitions.
            services: Optional service definitions.
            volumes: Optional volume definitions.

        Returns:
            A dictionary structure representing the Docker Compose file.
        """
        # self.module.log(msg=f"ComposeFile::create()")

        compose_dict: Dict[str, Any] = {}

        if version:
            compose_dict["version"] = version

        if networks:
            compose_dict["networks"] = networks

        if services:
            compose_dict["services"] = services

        if volumes:
            compose_dict["volumes"] = volumes

        return compose_dict

    def write(self, file_name: str, data: Dict[str, Any]) -> None:
        """
        Write the provided Compose data to a YAML file.

        Args:
            file_name: Destination path of the Compose file.
            data: Dictionary with Docker Compose configuration.

        Raises:
            self.module.fail_json: if the file cannot be written.
        """
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                self.yaml.dump(data, f)
            self.module.log(msg=f"Compose file successfully written to {file_name}")
        except (OSError, IOError) as err:
            self.module.fail_json(
                msg=f"Failed to write Compose file '{file_name}': {err}"
            )

    def validate(self, tmp_file: str, target_file: str) -> bool:
        """
        Compare two Compose files using checksum validation.

        Args:
            tmp_file: Temporary file path containing the new Compose data.
            target_file: Existing Compose file path to compare against.

        Returns:
            True if the content has changed (checksums differ), False otherwise.
        """
        checksum = Checksum(self.module)

        # Compute new checksum
        new_checksum = checksum.checksum_from_file(tmp_file)

        # Compute old checksum if file exists, else mark as changed
        if not os.path.exists(target_file):
            self.module.log(
                msg=f"Target file '{target_file}' does not exist; marking as changed."
            )
            return True

        old_checksum = checksum.checksum_from_file(target_file)
        changed = new_checksum != old_checksum

        self.module.log(
            msg=(
                f"Checksum validation for {target_file}: "
                f"{'changed' if changed else 'no change'} "
                f"(old={old_checksum}, new={new_checksum})"
            )
        )

        return changed
