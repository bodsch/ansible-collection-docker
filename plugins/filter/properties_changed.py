#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ansible.utils.display import Display

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
  name: properties_changed
  short_description: Return container property names that changed.
  version_added: "1.0.0"
  author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
  description:
    - Iterates over Ansible task results and returns the C(name) field from the
      C(item) dict for each entry where C(changed) is C(true).
  positional: _input
  options:
    _input:
      description: A dict with a C(results) key or a flat list of Ansible task result dictionaries.
      type: raw
      required: true
"""

EXAMPLES = r"""
- name: Get names of changed container properties
  ansible.builtin.debug:
    msg: "{{ loop_results | bodsch.docker.properties_changed }}"
"""

RETURN = r"""
  _value:
    description: List of container name strings where properties changed.
    type: list
    elements: str
"""

# ---------------------------------------------------------------------------------------


display = Display()


def filter_properties_changed(data):
    """Return container property names (item.name) where changed is True."""
    display.vv("filter_properties_changed(data)")

    if isinstance(data, dict):
        data = data.get("results", [])

    return [
        entry.get("item", {}).get("name")
        for entry in data
        if isinstance(entry, dict)
        and entry.get("changed", False)
        and entry.get("item", {}).get("name")
    ]


class FilterModule:
    def filters(self):
        return {"properties_changed": filter_properties_changed}
