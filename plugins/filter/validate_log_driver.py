#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any, Dict, Optional

from ansible.utils.display import Display

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
  name: validate_log_driver
  short_description: Validate a Docker log driver configuration.
  version_added: "1.0.0"
  author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
  description:
    - Checks whether the C(log_driver) value in the input dictionary is either
      a recognized Docker built-in driver or a correctly formatted custom plugin
      reference in the form C(<driver_name>:<driver_version>).
    - Built-in drivers are C(awslogs), C(fluentd), C(gcplogs), C(gelf),
      C(journald), C(json-file), C(local), C(logentries), C(splunk), C(syslog).
    - Custom drivers must follow the format C(name:version). Missing or empty
      version strings are treated as invalid.
  positional: _input
  options:
    _input:
      description:
        - Dictionary containing a C(log_driver) key with the driver value to validate.
      type: dict
      required: true
"""

EXAMPLES = r"""
- name: Validate a built-in log driver
  ansible.builtin.debug:
    msg: "{{ {'log_driver': 'json-file'} | bodsch.docker.validate_log_driver }}"
  # => {"valid": true, "msg": "valid"}

- name: Validate a custom log driver plugin
  ansible.builtin.debug:
    msg: "{{ {'log_driver': 'my-plugin:1.2.3'} | bodsch.docker.validate_log_driver }}"
  # => {"valid": true, "msg": "valid"}

- name: Detect invalid custom driver (missing version)
  ansible.builtin.debug:
    msg: "{{ {'log_driver': 'my-plugin'} | bodsch.docker.validate_log_driver }}"
  # => {"valid": false, "msg": "Invalid custom log driver format! ..."}

- name: Detect invalid custom driver (empty version)
  ansible.builtin.debug:
    msg: "{{ {'log_driver': 'my-plugin:'} | bodsch.docker.validate_log_driver }}"
  # => {"valid": false, "msg": "Missing plugin version! ..."}

- name: Fail task on invalid log driver
  ansible.builtin.fail:
    msg: "{{ log_driver_result.msg }}"
  vars:
    log_driver_result: "{{ container | bodsch.docker.validate_log_driver }}"
  when: not log_driver_result.valid
"""

RETURN = r"""
  _value:
    description: Validation result dictionary.
    type: dict
    contains:
      valid:
        description: C(true) if the log driver is valid, C(false) otherwise.
        type: bool
      msg:
        description: Descriptive message indicating the validation result or error.
        type: str
"""

# ---------------------------------------------------------------------------------------


display = Display()

_BUILT_IN_DRIVERS = frozenset(
    [
        "awslogs",
        "fluentd",
        "gcplogs",
        "gelf",
        "journald",
        "json-file",
        "local",
        "logentries",
        "splunk",
        "syslog",
    ]
)


def validate_log_driver(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the format and value of a Docker log driver configuration.

    Args:
        data (dict): Dictionary containing a ``log_driver`` key to validate.

    Returns:
        dict: Result with ``valid`` (bool) and ``msg`` (str).
    """
    display.vv(f"bodsch.docker.validate_log_driver({data})")

    log_driver: Optional[str] = data.get("log_driver")

    if log_driver and log_driver not in _BUILT_IN_DRIVERS:
        if ":" not in log_driver:
            return {
                "valid": False,
                "msg": (
                    "Invalid custom log driver format!\n"
                    "Expected format: <driver_name>:<driver_version>"
                ),
            }

        _, plugin_version = log_driver.split(":", 1)

        if not plugin_version.strip():
            return {
                "valid": False,
                "msg": (
                    "Missing plugin version!\n"
                    "Expected format: <driver_name>:<driver_version>"
                ),
            }

    return {"valid": True, "msg": "valid"}


class FilterModule:
    def filters(self) -> Dict[str, Any]:
        return {"validate_log_driver": validate_log_driver}
