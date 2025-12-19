#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2023, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
container_environments.py
=========================

An Ansible module for managing container environment files, property files,
and configuration files in various formats (YAML, JSON, TOML, INI).

This module automates the creation, update, and removal of configuration files
for containers (e.g., Docker, Podman, LXC). It ensures idempotency by using
checksum comparisons, supports multiple data formats, and automatically marks
containers for recreation when changes occur.

Features
--------
- Create, update, or remove environment and property files for containers.
- Write multi-format configuration files (YAML, JSON, TOML, INI).
- Idempotent operation through checksum verification.
- Optional diff generation for debugging and audits.
- Automatically sets `recreate=True` for changed container configurations.

This module is part of the `bodsch.docker` Ansible collection.
"""

from __future__ import absolute_import, division, print_function

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.checksum import Checksum
from ansible_collections.bodsch.core.plugins.module_utils.directory import (
    create_directory,
)
from ansible_collections.bodsch.core.plugins.module_utils.module_results import results
from ansible_collections.bodsch.core.plugins.module_utils.template.template import (
    write_template,
)
from ansible_collections.bodsch.docker.plugins.module_utils.config_backends import (
    INIWriter,
    JSONWriter,
    TOMLWriter,
    Writer,
    YAMLWriter,
)

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
---
module: container_environments
version_added: "1.0.0"
author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"

short_description: Manage environment and configuration files for containers.
description:
  - This module manages container environment definitions, property files, and configuration files.
  - It creates or updates files in a base directory structure (one subdirectory per container)
    and ensures idempotency using checksum comparisons.
  - The module supports multiple file formats (YAML, JSON, TOML, INI) for configuration data.
  - When container environments or configuration data change, the module reports C(changed=true)
    and marks the container entry with C(recreate=True).
  - Empty environment or property definitions result in file removal to maintain a clean state.

options:
  base_directory:
    description:
      - Base directory where container environment and configuration files will be stored.
      - Each container will have its own subdirectory under this path.
    required: true
    type: str

  container:
    description:
      - List of container configuration definitions.
      - Each entry defines environment variables, property files, or configuration files for a single container.
    required: true
    type: list
    elements: dict
    suboptions:
      name:
        description:
          - The container name.
          - Used as a directory name and as a prefix for environment and property files.
        required: true
        type: str
      environments:
        description:
          - A dictionary of environment variables for the container.
          - If empty, the environment file is removed.
        required: false
        type: dict
      properties:
        description:
          - A dictionary of Java-style key-value pairs to be written to a C(.properties) file.
        required: false
        type: dict
      property_files:
        description:
          - A list of additional property files to be written for the container.
          - Each element must contain C(name) and an optional C(properties) dictionary.
        required: false
        type: list
        elements: dict
      config_files:
        description:
          - A list of container configuration files to generate.
          - Each item can specify the file C(name), C(type), and C(data) content.
          - Supported types are C(yaml), C(json), C(toml), and C(ini).
        required: false
        type: list
        elements: dict
      recreate:
        description:
          - Added automatically by the module when environment or configuration changes are detected.
        returned: always
        type: bool
        default: false

  owner:
    description:
      - Owner of generated files.
    required: false
    type: str
  group:
    description:
      - Group of generated files.
    required: false
    type: str
  mode:
    description:
      - File permission mode in octal format (e.g., C(0644)).
    required: false
    type: str
  diff:
    description:
      - Enables file content diff generation for changed files (useful in check mode or debug).
    required: false
    type: bool
    default: false

notes:
  - The module ensures idempotency through checksum comparison.
  - Empty definitions result in removal of corresponding files.
  - The module supports multiple configuration formats (YAML, JSON, TOML, INI).
  - It does not manage service restarts automatically.
requirements:
  - Python >= 3.6
  - ansible-collection: bodsch.core
"""

EXAMPLES = r"""
# Example 1: Create environment and property files for multiple containers
- name: Manage environment and property files for containers
  bodsch.docker.container_environments:
    base_directory: /etc/container/environments
    container:
      - name: webapp
        environments:
          APP_ENV: production
          LOG_LEVEL: info
        properties:
          db.url: jdbc:mysql://db.internal:3306/web
          db.user: web
          db.password: secret
      - name: backend
        environments:
          DEBUG: "false"
          API_KEY: "XYZ-123"
        properties:
          cache.enabled: "true"

# Example 2: Generate multiple configuration files in different formats
- name: Create configuration files for container
  bodsch.docker.container_environments:
    base_directory: /opt/configs
    container:
      - name: myservice
        config_files:
          - name: settings.yaml
            type: yaml
            data:
              version: 1
              database:
                host: localhost
                port: 3306
          - name: settings.json
            type: json
            data:
              app: "myservice"
              debug: false

# Example 3: Remove files by setting empty data
- name: Remove container environment when empty
  bodsch.docker.container_environments:
    base_directory: /etc/container/environments
    container:
      - name: obsolete
        environments: {}
        properties: {}

# Example 4: Enable diff mode for audit or CI pipelines
- name: Show changes between generated and existing configurations
  bodsch.docker.container_environments:
    base_directory: /srv/configs
    container:
      - name: app
        environments:
          APP_MODE: staging
    diff: true
"""

RETURN = r"""
changed:
  description: Indicates whether any container environment or configuration files were created, modified, or removed.
  returned: always
  type: bool
  sample: true

failed:
  description: Whether module execution failed.
  returned: always
  type: bool
  sample: false

msg:
  description:
    - Human-readable message describing the outcome.
    - Includes per-container details for files written or updated.
  returned: always
  type: list
  sample:
    - webapp:
        state: "container.env, webapp.properties successful written"
        changed: true
    - backend:
        state: "container.env successful written"
        changed: true

container_data:
  description:
    - Final processed container configuration data including C(recreate) flags.
  returned: always
  type: list
  sample:
    - name: webapp
      recreate: true
      properties:
        db.url: jdbc:mysql://db.internal:3306/web
        db.user: web
      environments:
        APP_ENV: production
        LOG_LEVEL: info

diff:
  description:
    - Difference output between old and new files when C(diff=true).
  returned: when diff is enabled
  type: dict
  sample:
    webapp:
      container.env:
        added: ["NEW_VAR=value"]
        removed: ["OLD_VAR=value"]
"""

# ---------------------------------------------------------------------------------------

TPL_ENV = """# generated by ansible

{% for key, value in item.items() %}
{{ key }}={{ value }}
{% endfor %}

"""

TPL_PROP = """# generated by ansible

{% for key, value in item.items() %}
{{ key.ljust(30) }} = {{ value }}
{% endfor %}

"""


class ContainerEnvironments:
    """
    Manage environment and configuration files for containers.

    This class handles the creation, update, and removal of configuration files
    for containerized services. It supports generating `.env`, `.properties`,
    and multi-format configuration files such as YAML, JSON, TOML, or INI.

    The class ensures idempotency using checksum comparison and can mark
    containers as `recreate=True` if any file changes are detected.

    Attributes:
        module (AnsibleModule): The current Ansible module instance.
        base_directory (str): Base directory for all container configuration files.
        container (list): List of container configurations.
        owner (str): Owner for generated files (optional).
        group (str): Group for generated files (optional).
        mode (str): File permission mode (optional).
        diff (bool): Whether to generate file diffs for changed files.
        tmp_directory (str): Temporary directory for intermediate file generation.
    """

    module: AnsibleModule
    base_directory: str
    container: List[Dict[str, Any]]
    owner: Optional[str]
    group: Optional[str]
    mode: Optional[str]
    diff: bool
    tmp_directory: str
    checksum: Checksum

    def __init__(self, module: AnsibleModule) -> None:
        """
        Initialize the ContainerEnvironments manager.

        Args:
            module (AnsibleModule): The active Ansible module instance.

        Prepares paths, temporary directories, and module parameters for processing.
        """
        self.module = module
        self.base_directory = module.params.get("base_directory", "")
        self.container = module.params.get("container", [])
        self.owner = module.params.get("owner")
        self.group = module.params.get("group")
        self.mode = module.params.get("mode")
        self.diff = bool(module.params.get("diff", False))

        pid = os.getpid()
        self.tmp_directory = os.path.join(
            "/run/.ansible", f"container_environments.{pid}"
        )

    # --------------------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """
        Execute the main module logic.

        Iterates through all provided container definitions, writes environment,
        property, and configuration files as necessary, and determines whether
        changes occurred.

        Returns:
            dict: An Ansible result dictionary containing:
                - changed (bool): Whether files were changed.
                - failed (bool): Whether execution failed.
                - container_data (list): Final processed container data.
                - msg (list): Detailed result messages.
        """
        result: Dict[str, Any] = {"changed": False, "failed": True, "msg": "initial"}

        self.checksum = Checksum(self.module)
        create_directory(directory=self.tmp_directory, mode="0750")

        result_state: List[Dict[str, Any]] = []

        for c in self.container:
            name: str = c.get("name", "")
            environments: Dict[str, Any] = c.get("environments", {}) or {}
            properties: Dict[str, Any] = c.get("properties", {}) or {}
            property_files: List[Dict[str, Any]] = c.get("property_files", []) or []
            config_files: List[Dict[str, Any]] = c.get("config_files", []) or []

            defined_environments = bool(environments)
            defined_properties = bool(properties)
            defined_property_files = bool(property_files)
            defined_config_files = bool(config_files)

            tmp_directory = os.path.join(self.tmp_directory, name)
            create_directory(directory=tmp_directory, mode="0750")

            changed = False
            e_changed = False
            p_changed = False
            state: List[str] = []

            # ------------------------------------------------------------------
            # Write environments
            e_changed, _ = self._write_environments(
                container_name=name, environments=environments
            )

            if defined_environments:
                c.pop("environments", None)

            if e_changed:
                state.append("container.env")

            # ------------------------------------------------------------------
            # Write properties and property files
            if defined_properties or defined_property_files:
                property_filename = f"{name}.properties"
                property_files.append(
                    {"name": property_filename, "properties": properties}
                )

                for prop in property_files:
                    property_filename = prop.get("name", "")
                    prop_data = prop.get("properties", {}) or {}

                    _changed, _ = self._write_properties(
                        container_name=name,
                        property_filename=property_filename,
                        properties=prop_data,
                    )

                    if _changed:
                        p_changed = True
                        state.append(property_filename)

                c.pop("properties", None)
                c.pop("property_files", None)

            # ------------------------------------------------------------------
            # Write config files
            if defined_config_files:
                for cfg in config_files:
                    config_filename: str = cfg.get("name", "")
                    config_data: Dict[str, Any] = cfg.get("data", {}) or {}
                    config_type: str = cfg.get("type", "yaml")

                    _changed, _ = self._write_config(
                        container_name=name,
                        filename=config_filename,
                        config_type=config_type,
                        data=config_data,
                    )

                    if _changed:
                        p_changed = True
                        state.append(config_filename)

                c.pop("config_files", None)

            # ------------------------------------------------------------------
            if e_changed or p_changed:
                changed = True
                c["recreate"] = True

                result_state.append(
                    {
                        name: {
                            "state": f"{', '.join(state)} successfully written",
                            "changed": True,
                        }
                    }
                )

        # Aggregate results
        _state, _changed, _failed, state, changed, failed = results(
            self.module, result_state
        )

        result = {
            "changed": _changed,
            "failed": False,
            "container_data": self.container,
            "msg": result_state,
        }

        shutil.rmtree(self.tmp_directory)
        return result

    # --------------------------------------------------------------------------

    def _write_environments(
        self, container_name: str, environments: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Write environment file (.env) for the given container.

        Args:
            container_name (str): Container name.
            environments (dict): Key-value environment variables.

        Returns:
            tuple:
                - changed (bool): Whether the environment file changed.
                - difference (str): Optional diff output.
        """
        environments = environments or {}
        tmp_directory = os.path.join(self.tmp_directory, container_name)
        checksum_file = os.path.join(
            self.base_directory, container_name, "container.env.checksum"
        )
        data_file = os.path.join(self.base_directory, container_name, "container.env")
        difference = ""

        if os.path.exists(checksum_file):
            os.remove(checksum_file)

        tmp_file = os.path.join(tmp_directory, f"{container_name}.env")
        self.__write_template("environments", environments, tmp_file)

        new_checksum = self.checksum.checksum_from_file(tmp_file)
        old_checksum = self.checksum.checksum_from_file(data_file)
        changed = new_checksum != old_checksum

        if changed:
            self.__write_template("environments", environments, data_file)

        return changed, difference

    # --------------------------------------------------------------------------

    def _write_properties(
        self,
        container_name: str,
        property_filename: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Write a properties file for the given container.

        Args:
            container_name (str): Container name.
            property_filename (str): File name for the property file.
            properties (dict): Property key-value pairs.

        Returns:
            tuple:
                - changed (bool): Whether the property file changed.
                - difference (str): Optional diff output.
        """
        properties = properties or {}
        tmp_directory = os.path.join(self.tmp_directory, container_name)
        checksum_file = os.path.join(
            self.base_directory, container_name, f"{property_filename}.checksum"
        )
        data_file = os.path.join(self.base_directory, container_name, property_filename)
        difference = ""

        if os.path.exists(checksum_file):
            os.remove(checksum_file)

        if not properties:
            if os.path.exists(data_file):
                os.remove(data_file)
            return False, difference

        tmp_file = os.path.join(tmp_directory, property_filename)
        self.__write_template("properties", properties, tmp_file)
        new_checksum = self.checksum.checksum_from_file(tmp_file)
        old_checksum = self.checksum.checksum_from_file(data_file)
        changed = new_checksum != old_checksum

        if changed:
            self.__write_template("properties", properties, data_file)

        return changed, difference

    # --------------------------------------------------------------------------

    def _write_config(
        self,
        container_name: str,
        filename: str,
        config_type: str = "yaml",
        data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Write configuration files for the given container.

        Args:
            container_name (str): Container name.
            filename (str): Target configuration file name.
            config_type (str): Configuration type (yaml, json, toml, ini).
            data (dict): Configuration data.

        Returns:
            tuple:
                - changed (bool): Whether configuration changed.
                - difference (str): Optional diff output.
        """
        data = data or {}
        tmp_directory = os.path.join(self.tmp_directory, container_name)
        checksum_file = os.path.join(
            self.base_directory, container_name, f"{filename}.checksum"
        )
        data_file = os.path.join(self.base_directory, container_name, filename)
        difference = ""

        if os.path.exists(checksum_file):
            os.remove(checksum_file)

        if not data:
            if os.path.exists(data_file):
                os.remove(data_file)
            return False, difference

        # tmp_file = os.path.join(tmp_directory, filename)
        config_writer = self.resolve_writer(config_type)
        text = config_writer.dump(data)

        with tempfile.NamedTemporaryFile(
            "w", delete=False, dir=tmp_directory, encoding="utf-8"
        ) as tmp:
            tmp.write(text)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = Path(tmp.name)

            new_checksum = self.checksum.checksum_from_file(tmp_path)
            old_checksum = self.checksum.checksum_from_file(data_file)
            changed = new_checksum != old_checksum

            if changed:
                shutil.move(tmp_path, data_file)

        return changed, difference

    # --------------------------------------------------------------------------

    def __write_template(
        self,
        env: str,
        data: Dict[str, Any],
        data_file: str,
        checksum: Optional[str] = None,
        checksum_file: Optional[str] = None,
    ) -> None:
        """
        Write an environment or property file using Jinja2 templates.

        Args:
            env (str): Type of template ('environments' or 'properties').
            data (dict): Template data dictionary.
            data_file (str): Path where the file will be written.
            checksum (str, optional): Optional checksum for verification.
            checksum_file (str, optional): Path to store checksum.
        """
        tpl = TPL_ENV if env == "environments" else TPL_PROP
        write_template(data_file, tpl, data)

        if checksum and checksum_file:
            self.checksum.write_checksum(checksum_file, checksum)

    # --------------------------------------------------------------------------

    def resolve_writer(self, file_type: str) -> Writer:
        """
        Return the correct configuration writer class for the given file type.

        Args:
            file_type (str): Type of configuration file ('yaml', 'json', 'toml', or 'ini').

        Returns:
            Writer: A writer object capable of dumping configuration data.

        Raises:
            ValueError: If the file type is unknown.
        """
        t = file_type.strip().lower()
        if t in ("yaml", "yml"):
            return YAMLWriter()
        if t == "json":
            return JSONWriter()
        if t == "toml":
            return TOMLWriter()
        if t == "ini":
            return INIWriter()
        raise ValueError(
            f"Unknown configuration type '{file_type}'. Allowed: yaml|yml|json|toml|ini"
        )


# ---------------------------------------------------------------------------------------


def main():
    """
    Entry point for the Ansible module.

    Defines module arguments, initializes the module, and executes it.
    """
    args = dict(
        base_directory=dict(required=True, type="str"),
        container=dict(required=True, type="list"),
        owner=dict(required=False),
        group=dict(required=False),
        mode=dict(required=False, type="str"),
        diff=dict(required=False, type="bool", default=False),
    )

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=True,
    )

    handler = ContainerEnvironments(module)
    result = handler.run()

    module.log(msg=f"= result: {result}")
    module.exit_json(**result)


if __name__ == "__main__":
    main()
