#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ansible.utils.display import Display

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
  name: files_available
  short_description: Extract items where stat.exists is True.
  version_added: "1.0.0"
  author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
  description:
    - Iterates over results from Ansible's C(stat) module and returns the C(item)
      value for each entry where C(stat.exists) is C(true).
  positional: _input
  options:
    _input:
      description: List of result dictionaries from the Ansible C(stat) module.
      type: list
      elements: dict
      required: true
"""

EXAMPLES = r"""
- name: Get paths of existing files
  ansible.builtin.debug:
    msg: "{{ stat_results.results | bodsch.docker.files_available }}"
"""

RETURN = r"""
  _value:
    description: List of item values where stat.exists is true.
    type: list
"""

# ---------------------------------------------------------------------------------------


display = Display()


def files_available(data):
    """Return items from stat results where stat.exists is True."""
    display.vv(f"files_available({data})")
    return [
        entry.get("item")
        for entry in data
        if isinstance(entry, dict) and entry.get("stat", {}).get("exists", False)
    ]


class FilterModule:
    def filters(self):
        return {"files_available": files_available}
