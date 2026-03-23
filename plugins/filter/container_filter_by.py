#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ansible.utils.display import Display

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
  name: container_filter_by
  short_description: Filter containers by a given key and a list of allowed values.
  version_added: "1.0.0"
  author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
  description:
    - Returns only those container definitions where the specified key matches
      one of the provided allowed values.
    - Supported filter keys are C(name), C(hostname), and C(image).
  positional: _input, filter_by, filter_values
  options:
    _input:
      description: List of container definition dictionaries.
      type: list
      elements: dict
      required: true
    filter_by:
      description: The key to filter containers by.
      type: str
      choices: [name, hostname, image]
      required: true
    filter_values:
      description: List of allowed values to match against.
      type: list
      elements: str
      required: true
"""

EXAMPLES = r"""
- name: Filter containers by name
  ansible.builtin.debug:
    msg: "{{ containers | bodsch.docker.container_filter_by('name', ['nginx', 'redis']) }}"
"""

RETURN = r"""
  _value:
    description: Filtered list of container dictionaries.
    type: list
    elements: dict
"""

# ---------------------------------------------------------------------------------------


display = Display()

_ALLOWED_KEYS = {"name", "hostname", "image"}


def container_filter_by(data, filter_by, filter_values):
    """Filter containers by a given key and a list of allowed values."""
    display.vv(f"container_filter_by(data, {filter_by}, {filter_values})")
    if filter_by not in _ALLOWED_KEYS:
        return data
    return [
        entry
        for entry in data
        if isinstance(entry, dict) and entry.get(filter_by) in filter_values
    ]


class FilterModule:
    def filters(self):
        return {"container_filter_by": container_filter_by}
