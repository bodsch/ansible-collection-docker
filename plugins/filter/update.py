#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ansible.utils.display import Display

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
  name: update
  short_description: Add recreate=true to changed container entries.
  version_added: "1.0.0"
  author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
  description:
    - Marks container definitions for recreation by setting C(recreate=true) on
      any entry whose C(image) or C(name) matches an entry in the C(update) list.
  positional: _input, update
  options:
    _input:
      description: List of container definition dictionaries.
      type: list
      elements: dict
      required: true
    update:
      description: List of container names or image identifiers to flag for recreation.
      type: list
      elements: str
      required: true
"""

EXAMPLES = r"""
- name: Mark containers for recreation
  ansible.builtin.debug:
    msg: "{{ containers | bodsch.docker.update(['nginx:latest', 'my-app']) }}"
"""

RETURN = r"""
  _value:
    description: Updated list of container dictionaries with recreate=true where applicable.
    type: list
    elements: dict
"""

# ---------------------------------------------------------------------------------------


display = Display()


def filter_update(data, update):
    """Add recreate=true to container entries matching names or images in update list."""
    display.vv(f"filter_update(data, {update})")

    for change in update:
        for container in data:
            if container.get("image") == change or container.get("name") == change:
                container["recreate"] = "true"

    return data


class FilterModule:
    def filters(self):
        return {"update": filter_update}
