#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2023, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
docker_client_configs.py
========================

An Ansible module that manages Docker client configuration files (`config.json`)
for one or more users.

The module supports creation, update, and removal of Docker client configuration files,
handling user authentication for multiple registries and Docker CLI output formatting.

Features:
---------
- Idempotent creation of Docker client configuration files.
- Validation and encoding of Docker registry credentials.
- Flexible format configuration for CLI commands (`ps`, `images`, `plugins`, etc.).
- Safe handling of file permissions, ownership, and directory creation.
- Optional removal of existing configurations when `state=absent`.
- Ensures correctness through checksum-based change detection.

This module is part of the `bodsch.docker` Ansible collection.
"""


from __future__ import absolute_import, division, print_function

import base64
import grp
import json
import os
import pwd
import shutil
from typing import Any, Dict, List, Optional, Tuple

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.checksum import Checksum
from ansible_collections.bodsch.core.plugins.module_utils.directory import (
    create_directory,
)
from ansible_collections.bodsch.core.plugins.module_utils.module_results import results

__metaclass__ = type

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
---
module: docker_client_configs
version_added: "1.0.0"
author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"

short_description: Manage Docker client configuration files.
description:
  - This module manages Docker client configuration files (C(config.json))
    for one or more users.
  - It supports authentication to multiple registries, format customization
    for Docker CLI output, and ensures idempotent file creation based on checksum comparison.
  - The module can remove existing configurations, update credentials,
    or create new client configuration files.
  - Each configuration is validated for correctness, including Base64-encoded
    authentication strings or username/password pairs.

options:
  configs:
    description:
      - A list of Docker client configuration definitions.
      - Each configuration entry describes a separate Docker client configuration file.
    required: true
    type: list
    elements: dict
    suboptions:
      location:
        description:
          - The absolute file path where the Docker client configuration file
            (C(config.json)) will be written.
        required: true
        type: str
      state:
        description:
          - Desired state of the configuration file.
          - C(present) creates or updates the configuration.
          - C(absent) removes the configuration file and its checksum entry.
        required: false
        type: str
        choices: ["present", "absent"]
        default: "present"
      enabled:
        description:
          - Whether configuration creation is enabled.
          - When set to C(false), the module skips file creation
            but reports if a configuration already exists.
        required: false
        type: bool
        default: true
      owner:
        description:
          - Owner of the generated configuration file.
        required: false
        type: str
      group:
        description:
          - Group owner of the generated configuration file.
        required: false
        type: str
      mode:
        description:
          - File permission mode for the configuration file.
        required: false
        type: str
        default: "0644"
      auths:
        description:
          - A dictionary defining registry authentication information.
          - Each key represents a registry URL or hostname.
          - Authentication may be specified as a Base64-encoded C(auth) string,
            or as a combination of C(username) and C(password).
        required: false
        type: dict
        suboptions:
          auth:
            description:
              - Base64-encoded authentication string in the format C(username:password).
            required: false
            type: str
          username:
            description:
              - Docker registry username.
            required: false
            type: str
          password:
            description:
              - Docker registry password.
            required: false
            type: str
      formats:
        description:
          - Custom output format definitions for Docker CLI commands.
          - Each key defines the command (e.g., C(ps), C(images), C(plugins))
            and the value is a list of format fields to include in the output table.
        required: false
        type: dict
        suboptions:
          ps:
            description: Custom output fields for C(docker ps).
            type: list
            elements: str
          images:
            description: Custom output fields for C(docker images).
            type: list
            elements: str
          plugins:
            description: Custom output fields for C(docker plugin ls).
            type: list
            elements: str

notes:
  - Automatically creates missing directories for configuration destinations.
  - Validates authentication definitions to avoid conflicting or incomplete credentials.
  - Uses checksum comparison to ensure idempotency.
  - Compatible with Linux-based systems.

requirements:
  - Python >= 3.6
  - ansible-collection: bodsch.core
"""

EXAMPLES = r"""
# Example 1: Create a Docker client configuration for root
- name: Create Docker client configuration for root
  bodsch.docker.docker_client_configs:
    configs:
      - location: /root/.docker/config.json
        state: present
        auths:
          registry.gitlab.com:
            username: myuser
            password: mypassword
        formats:
          ps:
            - ".ID"
            - ".Names"
            - ".Status"
            - ".RunningFor"
            - ".Ports"

# Example 2: Create configuration for multiple users
- name: Configure Docker for multiple users
  bodsch.docker.docker_client_configs:
    configs:
      - location: /home/alice/.docker/config.json
        auths:
          registry.example.org:
            auth: amVua2luczpzZWNyZXQ=
      - location: /home/bob/.docker/config.json
        auths:
          registry.example.org:
            username: bob
            password: correcthorsebatterystaple

# Example 3: Disable configuration creation (keep existing)
- name: Skip configuration creation but verify file existence
  bodsch.docker.docker_client_configs:
    configs:
      - location: /root/.docker/config.json
        enabled: false

# Example 4: Remove existing configuration
- name: Remove Docker client configuration
  bodsch.docker.docker_client_configs:
    configs:
      - location: /root/.docker/config.json
        state: absent
"""

RETURN = r"""
changed:
  description: Indicates if any configuration files were created, modified, or removed.
  returned: always
  type: bool
  sample: true

failed:
  description: Whether the module execution failed.
  returned: always
  type: bool
  sample: false

msg:
  description:
    - Human-readable message describing the outcome of each configuration action.
    - Can contain a list of per-file results when multiple configurations are processed.
  returned: always
  type: list
  sample:
    - /root/.docker/config.json: "The Docker Client configuration was successfully created."
    - /home/bob/.docker/config.json: "The Docker Client configuration has not been changed."

invalid_authentications:
  description:
    - A list of invalid registry authentication entries that failed validation.
  returned: when authentication validation fails
  type: list
  sample:
    - registry.example.org:
        failed: true
        state: "Either the 'username' or 'password' is missing."

checksum:
  description:
    - Checksum of the generated configuration file.
  returned: when configuration file is written
  type: str
  sample: "5f2a53e9c1e839e7b8e42842d0e7b0c2"
"""

# ---------------------------------------------------------------------------------------

"""
  creates an user configuration like this:

{
  "auths": {
    "registry.gitlab.com": {
        "auth": "amVua2luczpydWJiZWwtZGllLWthdHotZHUtZHVtbXNjaHfDpHR6ZXIxCg=="
    }
  },
  "psFormat": "table {{.ID}}:\\t{{.Names}}\\t{{.Status}}\\t{{.RunningFor}}\\t{{.Ports}}"",
  "imagesFormat": "table {{.ID}}\\t{{.Repository}}\\t{{.Tag}}\\t{{.CreatedAt}}"
}

"""

# ---------------------------------------------------------------------------------------


class DockerClientConfigs(object):
    """
    Manage Docker client configuration files (`config.json`) for one or more users.

    This class provides methods for creating, updating, and removing Docker client
    configurations in an idempotent manner. It supports registry authentication
    (Base64 `auth` strings or username/password pairs) and Docker CLI output format
    customization for commands such as `docker ps`, `docker images`, and `docker plugins`.

    Attributes:
        module (AnsibleModule): The active Ansible module instance.
        configs (list): A list of configuration dictionaries provided by the user.
        tmp_directory (str): Temporary directory for intermediate file storage.
        cache_directory (str): Directory used to store checksum cache files.

    Typical workflow:
        1. Validate and process input configuration list.
        2. Handle authentication and format sections.
        3. Create or update Docker client configuration files.
        4. Compute checksums and determine changes.
        5. Optionally remove files when `state=absent`.
    """

    def __init__(self, module: AnsibleModule) -> None:
        """
        Initialize a new DockerClientConfigs instance.

        Args:
            module (AnsibleModule): The current Ansible module instance.

        Sets up temporary directories and caches required for checksum comparison
        and intermediate file operations.
        """
        self.module = module
        self.configs: List[Dict[str, Any]] = module.params.get("configs")
        pid = os.getpid()
        self.tmp_directory: str = os.path.join(
            "/run/.ansible", f"docker_client_configs.{str(pid)}"
        )
        self.cache_directory: str = "/var/cache/ansible/docker"

        # TODO
        # maybe later?
        # valid_formate_entries = [
        #     '.ID', '.Repository', '.Tag', '.CreatedAt', '.Names', '.Image', '.Command', '.Labels',
        #     '.Status', '.RunningFor', '.Ports'
        # ]

    def run(self) -> Dict[str, Any]:
        """
        Main module execution entry point.

        Iterates over all provided configuration entries and delegates processing
        to the `client()` method. Collects results from all configurations,
        determines overall module state (changed/failed), and cleans up temporary files.

        Returns:
            dict: Ansible result dictionary containing:
                - changed (bool): Whether any configurations changed.
                - failed (bool): Whether any configuration failed.
                - msg (list): List of per-file result dictionaries.
        """
        create_directory(directory=self.tmp_directory, mode="0750")

        self.checksum = Checksum(self.module)

        result_state: List[Dict[str, Any]] = []

        for conf in self.configs:
            destination = conf.get("location", None)

            if destination:
                result_state.append({destination: self.client(conf)})

        # define changed for the running tasks
        _state, _changed, _failed, state, changed, failed = results(
            self.module, result_state
        )

        result = dict(changed=_changed, failed=_failed, msg=result_state)

        try:
            shutil.rmtree(self.tmp_directory)
        except FileNotFoundError:
            pass

        return result

    def client(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single Docker client configuration definition.

        Handles authentication setup, Docker CLI format configuration, file creation,
        checksum comparison, permission management, and file removal (when state=absent).

        Args:
            client_data (dict): The configuration dictionary containing fields such as
                - location (str)
                - auths (dict with dicts)
                - formats (dict)
                - owner (str)
                - group (str)
                - mode (str)
                - state (str: 'present' or 'absent')
                - enabled (bool)
        Example:
        {
            'location': '/root/.docker/config.json',
            'enabled': True,
            'auths': {
                'registry.gitfoo.tld': {
                    'auth': 'amVua2luczpydWJiZWwtZGllLWthdHotZHUtZHVtbXNjaHfDpHR6ZXIxCg=='
                },
                'test.tld': {'username': 'FOO-was-sonst', 'passwort': 'ja-toll-schon-wieder-alles-scheisse!'}},
            'formats': {}
        }

        Returns:
            dict: Result dictionary describing the outcome for the given configuration,
            including keys:
                - changed (bool)
                - failed (bool)
                - msg (str)
        """
        self._validate_client_data(client_data)

        destination = client_data["location"]
        state = client_data.get("state", "present")
        enabled = client_data.get("enabled", True)
        owner = client_data.get("owner")
        group = client_data.get("group")
        mode = client_data.get("mode", "0644")

        auths = client_data.get("auths", {})
        formats = client_data.get("formats", {})

        location_directory = os.path.dirname(destination)
        hashed_dest = self.checksum.checksum(destination)
        checksum_file_name = os.path.join(
            self.cache_directory, f"client_{hashed_dest}.checksum"
        )

        self._cleanup_checksum_file(checksum_file_name, destination)

        if state == "absent":
            return self._remove_configuration(destination, checksum_file_name)

        if not enabled:
            msg = (
                "The creation of the Docker Client configuration has been deactivated."
            )
            if os.path.isfile(destination):
                msg += "\nHowever, a configuration file already exists. Use 'state=absent' to remove it."
            return dict(failed=False, changed=False, msg=msg)

        create_directory(
            directory=location_directory, mode="0750", owner=owner, group=group
        )

        invalid_auths, valid_auths = self._handle_authentications(auths)
        formats_cfg = self._handle_formats(formats)

        if invalid_auths:
            return dict(failed=True, msg=invalid_auths)

        data = {**valid_auths, **formats_cfg}

        tmp_file = os.path.join(self.tmp_directory, f"client_{hashed_dest}")
        self._write_json(tmp_file, data)

        new_checksum = self.checksum.checksum_from_file(tmp_file)
        old_checksum = self.checksum.checksum_from_file(destination)

        changed = new_checksum != old_checksum
        new_file = old_checksum is None

        if changed:
            self._write_json(destination, data)
            msg = (
                "The Docker Client configuration was successfully created."
                if new_file
                else "The Docker Client configuration was successfully updated."
            )
        else:
            msg = "The Docker Client configuration has not been changed."

        if os.path.isfile(destination):
            self._change_owner(destination, owner, group, mode)

        return dict(changed=changed, failed=False, msg=msg)

        # destination = client_data.get("location", None)
        # state = client_data.get("state", "present")
        # auths = client_data.get("auths", {})
        # formats = client_data.get("formats", {})
        # enabled = client_data.get("enabled", True)
        # owner = client_data.get("owner", None)
        # group = client_data.get("group", None)
        # mode = client_data.get("mode", "0644")
        #
        # location_directory = os.path.dirname(destination)
        #
        # hashed_dest = self.checksum.checksum(destination)
        # # checksum_file is obsolete
        # checksum_file_name = os.path.join(
        #     self.cache_directory, f"client_{hashed_dest}.checksum"
        # )
        #
        # if os.path.exists(checksum_file_name):
        #     os.remove(checksum_file_name)
        #
        # if state == "absent":
        #     """
        #     remove created files
        #     """
        #     config_file_exist = False
        #     config_checksum_exists = False
        #     msg = "The Docker Client configuration does not exist."
        #
        #     if os.path.isfile(destination):
        #         config_file_exist = True
        #         os.remove(destination)
        #         msg = "The Docker Client configuration has been removed."
        #
        #     if os.path.isfile(checksum_file_name):
        #         config_checksum_exists = True
        #         os.remove(checksum_file_name)
        #
        #     return dict(
        #         changed=(config_file_exist & config_checksum_exists),
        #         failed=False,
        #         msg=msg,
        #     )
        #
        # if not enabled:
        #     msg = (
        #         "The creation of the Docker Client configuration has been deactivated."
        #     )
        #
        #     if os.path.isfile(destination):
        #         msg += "\nBut the configuration file has already been created!\nTo finally remove it, the 'state' must be configured to 'absent'."
        #
        #     return dict(failed=False, changed=False, msg=msg)
        #
        # if not destination:
        #     return dict(failed=True, msg="No location has been configured.")
        #
        # if state not in ["absent", "present"]:
        #     return dict(
        #         failed=True,
        #         msg=f"Wrong state '{state}'. Only these are supported: 'absent', 'present'.",
        #     )
        #
        # if not isinstance(auths, dict):
        #     return dict(failed=True, msg="'auths' must be an dictionary.")
        #
        # if not isinstance(formats, dict):
        #     return dict(failed=True, msg="'formats' must be an dictionary.")
        #
        # # create destination directory
        # create_directory(
        #     directory=location_directory, mode="0750", owner=owner, group=group
        # )
        # create_directory(directory=self.tmp_directory, mode="0750")
        #
        # if not os.path.isfile(destination):
        #     """
        #     clean manual removements
        #     """
        #     if os.path.isfile(checksum_file_name):
        #         os.remove(checksum_file_name)
        #
        # invalid_authentications, authentications = self._handle_authentications(auths)
        # formats = self._handle_formats(formats)
        #
        # if len(invalid_authentications) > 0:
        #     return dict(failed=True, msg=invalid_authentications)
        #
        # data = {**authentications, **formats}
        #
        # tmp_file = os.path.join(self.tmp_directory, f"client_{hashed_dest}")
        #
        # self.__write_config(tmp_file, data)
        # new_checksum = self.checksum.checksum_from_file(tmp_file)
        # old_checksum = self.checksum.checksum_from_file(destination)
        # changed = not (new_checksum == old_checksum)
        # new_file = False
        # msg = "The Docker Client configuration has not been changed."
        #
        # if changed:
        #     new_file = old_checksum is None
        #     self.__write_config(destination, data)
        #     msg = "The Docker Client configuration was successfully changed."
        #
        # if new_file:
        #     msg = "The Docker Client configuration was successfully created."
        #
        # if os.path.isfile(destination):
        #     self.change_owner(destination, owner, group, mode)
        #
        # return dict(changed=changed, failed=False, msg=msg)

    def _validate_client_data(self, data: Dict[str, Any]) -> None:
        """
        Validate the structure and required fields of a client configuration entry.

        Args:
            data (dict): The configuration dictionary to validate.

        Raises:
            fail_json: If required parameters are missing or invalid.
        """
        destination = data.get("location")
        if not destination:
            self.module.fail_json(msg="Missing required parameter: 'location'.")

        state = data.get("state", "present")
        if state not in ["present", "absent"]:
            self.module.fail_json(
                msg=f"Invalid state '{state}'. Expected 'present' or 'absent'."
            )

        for param in ["auths", "formats"]:
            if not isinstance(data.get(param, {}), dict):
                self.module.fail_json(msg=f"'{param}' must be a dictionary.")

    # --------------------------------------------------------------------------
    # File and Checksum Helpers
    # --------------------------------------------------------------------------

    def _cleanup_checksum_file(self, checksum_file: str, destination: str) -> None:
        """
        Remove obsolete checksum files if configuration file is missing.

        Args:
            checksum_file (str): Path to the checksum file.
            destination (str): Path to the target configuration file.
        """
        if os.path.exists(checksum_file):
            os.remove(checksum_file)

        if not os.path.isfile(destination) and os.path.isfile(checksum_file):
            os.remove(checksum_file)

    def _remove_configuration(
        self, destination: str, checksum_file: str
    ) -> Dict[str, Any]:
        """
        Remove a Docker client configuration and its checksum file.

        Args:
            destination (str): Configuration file path.
            checksum_file (str): Path to associated checksum file.

        Returns:
            dict: Result indicating whether a file was removed.
        """
        config_exists = os.path.isfile(destination)
        checksum_exists = os.path.isfile(checksum_file)

        if config_exists:
            os.remove(destination)
        if checksum_exists:
            os.remove(checksum_file)

        msg = (
            "The Docker Client configuration has been removed."
            if config_exists or checksum_exists
            else "The Docker Client configuration does not exist."
        )

        return dict(changed=config_exists or checksum_exists, failed=False, msg=msg)

    # --------------------------------------------------------------------------
    # Authentication and Format Handling
    # --------------------------------------------------------------------------

    def _handle_authentications(
        self, auths: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Validate and normalize Docker registry authentication entries.

        Args:
            auths (dict): Dictionary of registry authentication data.

        Returns:
            tuple:
                - invalid_auths (list): Invalid authentication entries with errors.
                - valid_auths (dict): Valid `auths` dictionary for config.json.
        """
        invalid = []
        valid_auths = {"auths": {}}

        for registry, creds in auths.items():
            valid, msg = self._validate_auth(creds)
            if not valid:
                invalid.append({registry: dict(failed=True, state=msg)})
                continue

            valid_auths["auths"][registry] = {"auth": self._encode_auth(creds)}

        return invalid, valid_auths

    def _validate_auth(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate an individual authentication entry.

        Args:
            data (dict): Dictionary containing `auth`, `username`, or `password`.

        Returns:
            tuple:
                - bool: Whether the authentication entry is valid.
                - str: Human-readable validation status message.
        """
        auth, username, password = (
            data.get("auth"),
            data.get("username"),
            data.get("password"),
        )

        if not auth and not (username or password):
            return True, "No authentication defined."

        if auth and not (username or password):
            return True, "Base64 authentication defined."

        if auth and (username and password):
            return False, "Define either 'auth' or 'username/password', not both."

        if not auth and (not username or not password):
            return False, "Both 'username' and 'password' must be set."

        return True, "Username/password authentication defined."

    def _encode_auth(self, data: Dict[str, Any]) -> str:
        """
        Encode registry credentials into Base64 format.

        Args:
            data (dict): Authentication data with `username` and `password`.

        Returns:
            str: Base64-encoded authentication string.
        """
        if "auth" in data:
            return data["auth"]

        token = f"{data['username']}:{data['password']}".encode("utf-8")
        return base64.standard_b64encode(token).decode("utf-8")

    def _handle_formats(self, formats: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Convert Docker CLI format definitions into string-based table formats.

        Args:
            formats (dict): Dictionary of CLI format definitions.

        Returns:
            dict: Dictionary mapping CLI command keys to table format strings.
        """
        result: Dict[str, str] = {}
        for section, fields in formats.items():
            if fields:
                table_str = "table " + "\\t".join([f"{{{{{f}}}}}" for f in fields])
                result[f"{section}Format"] = table_str

        return result

    # --------------------------------------------------------------------------
    # File Writing and Permissions
    # --------------------------------------------------------------------------

    def _write_json(self, path: str, data: Dict[str, Any]) -> None:
        """
        Write a dictionary to a JSON file in a human-readable format.

        Args:
            path (str): File path to write to.
            data (dict): Configuration dictionary.
        """
        with open(path, "w") as f:
            json.dump(data, f, indent=2, sort_keys=False)
            f.write("\n")

    def _change_owner(
        self, path: str, owner: Optional[str], group: Optional[str], mode: Optional[str]
    ) -> None:
        """
        Change file ownership and permissions for a configuration file.

        Args:
            path (str): Path to the configuration file.
            owner (str, optional): Owner username.
            group (str, optional): Group name.
            mode (str, optional): File mode as octal string.
        """
        if mode:
            os.chmod(path, int(mode, base=8))

        uid = pwd.getpwnam(owner).pw_uid if owner else 0
        gid = grp.getgrnam(group).gr_gid if group else 0

        if os.path.exists(path):
            os.chown(path, uid, gid)

    # FRIEDHOF

    def __handle_authentications(self, auths):
        """
        Validate and normalize authentication configuration.

        Ensures that each registry entry defines either a valid Base64-encoded
        `auth` string or a username/password combination. Invalid configurations
        are removed from the resulting output.

        Args:
            auths (dict): Registry authentication definitions.

        Returns:
            tuple:
                - invalid_authentications (list): List of invalid authentication entries.
                - auths_dict (dict): Valid `auths` dictionary ready for JSON output.

        possible  values:
          auths:
            registry.gitlab.com:
              auth: amVua2luczpydWJiZWwtZGllLWthdHotZHUtZHVtbXNjaHfDpHR6ZXIxCg==
            registry.githu.com:
              user: foobar
              password: vaulted_freaking_password

        """
        invalid_authentications = []

        copy_auths = auths.copy()

        for k, v in auths.items():
            """
            filter broken configs
            """
            res = {}
            valide, validate_msg = self.__validate_auth(v)

            if not valide:
                self.module.log(f" validation error: {validate_msg}")
                copy_auths.pop(k)

                res[k] = dict(failed=True, state=validate_msg)

                invalid_authentications.append(res)

        auths_dict = dict()
        auths_dict["auths"] = dict()

        for k, v in copy_auths.items():
            """
            Ensure that the auth string is a base64 encoded thing.
            the content of an existing base64 string is not checked here!
            """
            auth = self.__base64_auth(v)
            # self.module.log(f"   - {k} -> {auth}")
            auths_dict["auths"].update({k: {"auth": auth}})

        return invalid_authentications, auths_dict

    def __handle_formats(self, formats):
        """
        Convert Docker CLI format definitions into string-based configuration entries.

        Each CLI command (e.g., `ps`, `images`, `plugins`) is converted into a
        string representation suitable for Docker’s `config.json` file using the
        `table {{.Field}}` notation.

        Args:
            formats (dict): Dictionary of format definitions for Docker commands.

        Example:
          formats:
            ps:
              - ".ID"
              - ".Names"
              - ".Status"
              - ".RunningFor"
              - ".Ports"
              - ".Image"
              - ".Command"
              - ".Labels"
            images:
              - ".ID"
              - ".Image"
              - ".Command"
              - ".Labels"
            plugins:
              - ".ID"
              - ".Names"
              - ".Enabled"
            stats:
              - ".Container"
              - ".CPUPerc"
              - ".MemUsage"
            services:
              - ".ID"
              - ".Name"
              - ".Mode"
            secrets:
              - ".ID"
              - ".Name"
              - ".CreatedAt"
              - ".UpdatedAt"
            config:
              - ".ID"
              - ".Name"
              - ".CreatedAt"
              - ".UpdatedAt"
            nodes:
              - ".ID"
              - ".Hostname"
              - ".Availability"

        Returns:
            dict: A dictionary mapping CLI commands to formatted string keys.
        """

        def __format_to_string(t):
            """
            input:
              images:
                - ".ID"
                - ".Image"
                - ".Command"
                - ".Labels"
            result:
              - 'imagesFormat': 'table {{.ID}}\\t{{.Repository}}\\t{{.Tag}}\\t{{.CreatedAt}}'
            """
            _result = "table "
            for i, item in enumerate(t):
                _result += "{{{{{0}}}}}".format(item)
                if not i == len(t) - 1:
                    _result += "\\t"

            return _result

        result = {}

        for k, v in formats.items():
            if (
                k
                in [
                    "ps",
                    "images",
                    "plugins",
                    "stats",
                    "services",
                    "secret",
                    "config",
                    "nodes",
                ]
                and len(v) != 0
            ):
                result[f"{k}Format"] = __format_to_string(v)

        return result

    def __validate_auth(self, data):
        """
        Validate a single registry authentication entry.

        Ensures that the configuration uses either:
        - A valid Base64-encoded `auth` string, or
        - A `username` and `password` combination.

        Returns:
            tuple:
                - bool: True if the authentication entry is valid, False otherwise.
                - str: Description of the validation result.
        """

        auth = data.get("auth", None)
        username = data.get("username", None)
        password = data.get("password", None)

        return_result = False
        return_message = None

        if not auth and not username and not password:
            return_result = True
            return_message = "not authentication defined"

        if auth and (not username and not password):
            return_result = True
            return_message = "base64 authentication defined"

        if auth and (username and password):
            return_result = False
            return_message = "Only one variant can be defined!\nPlease choose between 'auth' or the combination of 'username' and 'password'!"

        if not auth and (not username or not password):
            return_result = False
            return_message = "Either the 'username' or the 'password' is missing!"

        if not auth and (username and password):
            return_result = True
            return_message = (
                "combination of 'username' and 'password' authentication defined"
            )

        # self.module.log(f"= {return_result}, {return_message})")
        return return_result, return_message

    def __base64_auth(self, data):
        """
        Encode username and password credentials into a Base64 authentication string.

        If an `auth` field is already provided, it is returned unchanged.

        Args:
            data (dict): Dictionary containing authentication information.

        Returns:
            str: Base64-encoded `auth` string for Docker registry authentication.
        """
        auth = data.get("auth", None)
        username = data.get("username", None)
        password = data.get("password", None)

        if auth:
            return auth

        d_bytes = f"{username}:{password}".encode("utf-8")

        base64_bytes = base64.standard_b64encode(d_bytes)
        base64_message = base64_bytes.decode("utf8")

        return base64_message

    def __write_config(self, file_name, data):
        """
        Write configuration data to a JSON file.

        Args:
            file_name (str): Path to the configuration file.
            data (dict): Dictionary containing configuration data.

        Writes the configuration in indented JSON format for human readability.
        """
        with open(file_name, "w") as fp:
            json_data = json.dumps(data, indent=2, sort_keys=False)
            fp.write(f"{json_data}\n")

    def __change_owner(self, destination, owner=None, group=None, mode=None):
        """
        Adjust file ownership and permissions for the Docker configuration file.

        Args:
            destination (str): Path to the configuration file.
            owner (str, optional): File owner name or UID.
            group (str, optional): File group name or GID.
            mode (str, optional): File permission mode (octal string, e.g., "0644").

        Performs safe conversions of user and group names to numeric IDs and updates
        permissions using `os.chmod()` and `os.chown()`.
        """
        if mode is not None:
            os.chmod(destination, int(mode, base=8))

        if owner is not None:
            try:
                owner = pwd.getpwnam(owner).pw_uid
            except KeyError:
                owner = int(owner)
                pass
        else:
            owner = 0

        if group is not None:
            try:
                group = grp.getgrnam(group).gr_gid
            except KeyError:
                group = int(group)
                pass
        else:
            group = 0

        if os.path.exists(destination) and owner and group:
            os.chown(destination, int(owner), int(group))


def main():
    """
    Ansible module entry point.

    Defines module argument specifications, initializes the DockerClientConfigs
    class, and executes the module logic.

    The function collects results and calls `exit_json()` to return results
    to Ansible.
    """
    args = dict(configs=dict(required=True, type=list))

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=True,
    )

    dcc = DockerClientConfigs(module)
    result = dcc.run()

    module.log(msg=f"= result: {result}")

    module.exit_json(**result)


# import module snippets
if __name__ == "__main__":
    main()
