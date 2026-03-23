#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ansible.utils.display import Display

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
  name: changed
  short_description: Return items from results where changed is True.
  version_added: "1.0.0"
  author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
  description:
    - Iterates over a list of Ansible task results (or a dict with a C(results) key)
      and returns the C(item) value for each entry where C(changed) is C(true).
  positional: _input
  options:
    _input:
      description: A dict with a C(results) key or a flat list of Ansible task result dictionaries.
      type: raw
      required: true
"""

EXAMPLES = r"""
- name: Get items that changed
  ansible.builtin.debug:
    msg: "{{ loop_results | bodsch.docker.changed }}"
"""

RETURN = r"""
  _value:
    description: List of item values from entries where changed is true.
    type: list
"""

# ---------------------------------------------------------------------------------------

display = Display()


def filter_changed(data):
    """Return items from task results where changed is True."""
    display.vv("filter_changed(data)")

    if isinstance(data, dict):
        data = data.get("results", [])

    return [
        entry.get("item")
        for entry in data
        if isinstance(entry, dict)
        and entry.get("changed", False)
        and entry.get("item") is not None
    ]


class FilterModule:
    def filters(self):
        return {"changed": filter_changed}
