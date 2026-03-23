#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ansible.utils.display import Display

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
  name: container_environnments
  short_description: Extract selected environment-related keys from container definitions.
  version_added: "1.0.0"
  author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
  description:
    - Filters each container dictionary to only include the keys specified in C(want_list).
    - Useful for passing a reduced view of container definitions to environment-handling tasks.
  positional: _input, want_list
  options:
    _input:
      description: List of container definition dictionaries.
      type: list
      elements: dict
      required: true
    want_list:
      description:
        - Keys to retain in the output.
        - Defaults to C([name, hostname, environments, properties, property_files, config_files]).
      type: list
      elements: str
      required: false
"""

EXAMPLES = r"""
- name: Extract environment keys from containers
  ansible.builtin.debug:
    msg: "{{ containers | bodsch.docker.container_environnments }}"

- name: Extract only name and environments
  ansible.builtin.debug:
    msg: "{{ containers | bodsch.docker.container_environnments(['name', 'environments']) }}"
"""

RETURN = r"""
  _value:
    description: List of dicts containing only the requested keys per container.
    type: list
    elements: dict
"""

# ---------------------------------------------------------------------------------------


display = Display()

_DEFAULT_WANT = [
    "name",
    "hostname",
    "environments",
    "properties",
    "property_files",
    "config_files",
]


def container_environnments(data, want_list=None):
    """Extract only selected environment-related keys from container definitions."""
    display.vv(f"container_environnments(data, {want_list})")
    if want_list is None:
        want_list = _DEFAULT_WANT
    return [{k: v for k, v in item.items() if k in want_list} for item in data]


class FilterModule:
    def filters(self):
        return {"container_environnments": container_environnments}
