#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ansible.errors import AnsibleFilterError
from ansible.utils.display import Display

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
  name: container_names
  short_description: Return a list of container names.
  version_added: "1.0.0"
  author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
  description:
    - Extracts the C(name) field from each container definition in the input list.
  positional: _input
  options:
    _input:
      description: List of container definition dictionaries.
      type: list
      elements: dict
      required: true
"""

EXAMPLES = r"""
- name: Get all container names
  ansible.builtin.debug:
    msg: "{{ containers | bodsch.docker.container_names }}"
"""

RETURN = r"""
  _value:
    description: List of container name strings.
    type: list
    elements: str
"""

# ---------------------------------------------------------------------------------------


display = Display()


def container_names(data):
    """Return a list of container names from a list of container dicts."""
    display.vv(f"container_names({data})")
    if not isinstance(data, list):
        raise AnsibleFilterError("container_names: expected a list of containers.")
    return [c.get("name") for c in data if "name" in c]


class FilterModule:
    def filters(self):
        return {"container_names": container_names}
