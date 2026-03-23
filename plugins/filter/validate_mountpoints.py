#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ansible.utils.display import Display

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
  name: validate_mountpoints
  short_description: Validate mountpoint definitions and detect missing attributes.
  version_added: "1.0.0"
  author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
  description:
    - Inspects each mount definition within a list of container definitions.
    - Returns a list of invalid mount entries, including the container name, the
      mount definition, and a description of the error.
    - A mount is considered invalid if any of C(source), C(target), or C(type) is
      missing, or if C(type) is not one of C(bind), C(tmpfs), or C(volume).
  positional: _input
  options:
    _input:
      description: List of container definition dictionaries, each potentially containing a C(mounts) key.
      type: list
      elements: dict
      required: true
"""

EXAMPLES = r"""
- name: Validate all mountpoints
  ansible.builtin.debug:
    msg: "{{ containers | bodsch.docker.validate_mountpoints }}"
"""

RETURN = r"""
  _value:
    description: List of invalid mount definitions with container name and error description.
    type: list
    elements: dict
"""

# ---------------------------------------------------------------------------------------


display = Display()

_VALID_TYPES = {"bind", "tmpfs", "volume"}


def validate_mountpoints(data):
    """Validate mountpoint definitions and detect missing or invalid attributes."""
    display.vv("validate_mountpoints(data)")
    errors = []
    for container in data:
        container_name = container.get("name")
        mounts = container.get("mounts", [])
        if not isinstance(mounts, list):
            continue
        for mount in mounts:
            if not isinstance(mount, dict):
                continue
            missing = [k for k in ("source", "target", "type") if not mount.get(k)]
            invalid_type = mount.get("type") not in _VALID_TYPES
            if missing or invalid_type:
                errors.append(
                    {
                        "container": container_name,
                        "mount_definition": mount,
                        "error": ", ".join(missing or ["wrong type"]),
                    }
                )
    display.vv(f"validate_mountpoints errors: {errors}")
    return errors


class FilterModule:
    def filters(self):
        return {"validate_mountpoints": validate_mountpoints}
