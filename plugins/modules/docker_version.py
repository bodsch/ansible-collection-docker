#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2023, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

"""
docker_version.py
=================

An Ansible module to retrieve the Docker Engine version and API version from a local or remote Docker daemon.

This module can connect to a Docker socket (e.g., `/run/docker.sock`) or use environment variables
to detect the active Docker daemon. It checks if Docker is available and returns the current engine
and API versions.

Features:
---------
- Detects whether Docker is running and accessible.
- Retrieves Docker Engine version and API version.
- Supports configurable Docker socket path.

This module is part of the `bodsch.docker` Ansible collection.
"""

from __future__ import absolute_import, division, print_function

import json
import os
from typing import Any, Dict, Optional

import docker
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
---
module: docker_version
author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
version_added: "1.0.0"

short_description: Retrieve the current Docker Engine and API version.
description:
  - This module checks if Docker is available and running.
  - It retrieves the Docker Engine version and API version from the Docker daemon.
  - If the Docker socket is not found or the daemon is unreachable, the module fails gracefully.

options:
  docker_socket:
    description:
      - Path to the Docker socket file used to connect to the Docker daemon.
      - If not specified, the module will attempt to use environment-based configuration.
    required: false
    type: str
    default: "/run/docker.sock"

  state:
    description:
      - Desired state of the module.
      - C(present) or C(test) are used for information gathering, while C(absent) is not applicable here.
    required: false
    type: str
    choices: ["absent", "present", "test"]
    default: "present"

notes:
  - Requires the C(docker) Python package (Docker SDK for Python).
  - Only reads information; it does not modify the Docker configuration or system state.
requirements:
  - Python >= 3.6
  - docker >= 4.0.0
"""

EXAMPLES = r"""
# Example 1: Retrieve Docker version information
- name: Get Docker Engine version
  bodsch.docker.docker_version:
    docker_socket: /run/docker.sock
  register: docker_info

- name: Display Docker version
  debug:
    msg: "Docker Engine version: {{ docker_info.versions.docker_version }}, API: {{ docker_info.versions.api_version }}"

# Example 2: Use environment variables for Docker connection
- name: Get Docker version using default environment configuration
  bodsch.docker.docker_version:

# Example 3: Run in test mode (no state change)
- name: Test Docker version module
  bodsch.docker.docker_version:
    state: test
"""

RETURN = r"""
changed:
  description: Whether the module made any changes (always False).
  type: bool
  returned: always
  sample: false

failed:
  description: Whether the operation failed.
  type: bool
  returned: always
  sample: false

versions:
  description: Dictionary containing Docker Engine and API versions.
  type: dict
  returned: when docker is running
  sample:
    api_version: "1.43"
    docker_version: "26.1.0"

msg:
  description: Message describing the result or any encountered error.
  type: str
  returned: when failed
  sample: "APIError: Cannot connect to the Docker daemon"
"""

# ---------------------------------------------------------------------------------------


class DockerVersion:
    """
    Retrieve and validate Docker daemon version information.

    This class encapsulates the logic for connecting to a Docker daemon
    and fetching version data via the Docker SDK.

    Attributes:
        module (AnsibleModule): The active Ansible module instance.
        state (str): Desired state (present, absent, test).
        docker_socket (str): Path to the Docker socket file.
    """

    def __init__(self, module: AnsibleModule) -> None:
        """
        Initialize the DockerVersion helper.

        Args:
            module: The active Ansible module instance.
        """
        self.module = module
        self.state: str = module.params.get("state")
        self.docker_socket: str = module.params.get("docker_socket")
        self.docker_client: Optional[docker.DockerClient] = None

    def run(self) -> Dict[str, Any]:
        """
        Execute the module logic to query Docker version information.

        Returns:
            dict: Result dictionary compatible with Ansible.
        """
        docker_status: bool = False
        docker_versions: Dict[str, Optional[str]] = {}
        error_msg: Optional[str] = None

        try:
            # Determine connection mode
            if os.path.exists(self.docker_socket):
                self.docker_client = docker.DockerClient(
                    base_url=f"unix://{self.docker_socket}"
                )
            else:
                self.docker_client = docker.from_env()

            # Verify Docker is reachable
            docker_status = self.docker_client.ping()

        except docker.errors.APIError as e:
            error_msg = f"Docker API error: {e}"
            self.module.log(error_msg)
        except docker.errors.DockerException as e:
            error_msg = f"Docker connection error: {e}"
            self.module.log(error_msg)
        except Exception as e:
            error_msg = f"Unexpected exception: {e}"
            self.module.log(error_msg)

        if not docker_status:
            return dict(
                changed=False,
                failed=True,
                msg=f"{error_msg or 'Docker daemon not reachable.'}",
            )

        # Retrieve version info
        docker_version = self.docker_client.version()
        if docker_version:
            docker_versions = {
                "api_version": docker_version.get("ApiVersion"),
                "docker_version": docker_version.get("Version"),
            }

        self.module.log(
            msg=f"Docker version information: {json.dumps(docker_versions, sort_keys=True)}"
        )

        return dict(changed=False, failed=False, versions=docker_versions)


def main() -> None:
    """
    Main entry point for the Ansible module.

    Initializes module parameters, executes the DockerVersion class,
    and returns results to Ansible.
    """

    args = dict(
        state=dict(default="present", choices=["absent", "present", "test"]),
        docker_socket=dict(required=False, type="str", default="/run/docker.sock"),
    )

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=True,
    )

    handler = DockerVersion(module)
    result = handler.run()

    module.log(msg=f"= result: {result}")

    module.exit_json(**result)


# import module snippets
if __name__ == "__main__":
    main()
