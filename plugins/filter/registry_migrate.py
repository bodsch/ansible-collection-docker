#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import operator as op

from ansible.utils.display import Display
from packaging.version import Version

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
  name: registry_migrate
  short_description: Migrate old registry configurations to a new schema.
  version_added: "1.0.0"
  author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
  description:
    - Inspects a registry configuration dictionary and updates deprecated keys.
    - For registry versions >= C(3.0), migrates the single C(addr) key to the
      list-based C(addrs) format if C(addrs) is not already present.
    - See U(https://github.com/distribution/distribution/commit/fcb2deac0b6d2e9c5f840dcebe580b46d4e99a0f).
  positional: _input, config_type, version
  options:
    _input:
      description: The registry configuration dictionary to migrate.
      type: dict
      required: true
    config_type:
      description: The registry configuration type (reserved for future use).
      type: str
      required: false
    version:
      description: The target registry version string (e.g. C("3.0.0")).
      type: str
      required: false
"""

EXAMPLES = r"""
- name: Migrate registry config to v3 schema
  ansible.builtin.debug:
    msg: "{{ registry_config | bodsch.docker.registry_migrate(omit, '3.1.0') }}"
"""

RETURN = r"""
  _value:
    description: Updated registry configuration dictionary.
    type: dict
"""

# ---------------------------------------------------------------------------------------


display = Display()


def _version_compare(ver1, specifier, ver2):
    lookup = {"<": op.lt, "<=": op.le, "==": op.eq, ">=": op.ge, ">": op.gt}
    try:
        return lookup[specifier](Version(ver1), Version(ver2))
    except (KeyError, Exception) as e:
        display.v(f"registry_migrate version compare error: {e}")
        return False


def registry_migrate(data, config_type=None, version=None):
    """Migrate old registry configurations to a new schema based on version."""
    display.vv(f"registry_migrate({data}, {config_type}, {version})")
    result = data.copy()
    if version and _version_compare(version, ">=", "3.0"):
        redis_addr = data.get("addr")
        redis_addrs = data.get("addrs")
        if redis_addr:
            result.pop("addr", None)
        if redis_addr and not redis_addrs:
            result["addrs"] = [redis_addr]
    return result


class FilterModule:
    def filters(self):
        return {"registry_migrate": registry_migrate}
