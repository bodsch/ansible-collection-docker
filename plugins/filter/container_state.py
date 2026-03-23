#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ansible.errors import AnsibleFilterError
from ansible.utils.display import Display

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
  name: container_state
  short_description: Filter containers by state and return a specific attribute.
  version_added: "1.0.0"
  author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
  description:
    - Filters container definitions by a given state and returns a sorted, deduplicated
      list of a specified attribute (e.g. C(image), C(name)).
    - States C(started) and C(present) are treated as equivalent.
    - States C(stopped) and C(absent) are treated as equivalent.
  positional: _input, state, return_value
  options:
    _input:
      description: List of container definition dictionaries.
      type: list
      elements: dict
      required: true
    state:
      description: The desired container state to filter by.
      type: str
      default: present
      choices: [started, stopped, present, absent]
    return_value:
      description: The attribute key to return for matched containers.
      type: str
      default: image
"""

EXAMPLES = r"""
- name: Get images for started containers
  ansible.builtin.debug:
    msg: "{{ containers | bodsch.docker.container_state('started', 'image') }}"
"""

RETURN = r"""
  _value:
    description: Sorted, deduplicated list of the requested attribute values.
    type: list
    elements: str
"""

# ---------------------------------------------------------------------------------------


display = Display()

_VALID_STATES = {"started", "stopped", "present", "absent"}
_PRESENT_STATES = {"started", "present"}
_ABSENT_STATES = {"stopped", "absent"}


def container_state(data, state="present", return_value="image"):
    """Filter containers by state and return a specific attribute."""
    display.vv(f"container_state({data}, {state}, {return_value})")
    if state not in _VALID_STATES:
        raise AnsibleFilterError(f"container_state: invalid state '{state}'.")
    state_filter = _PRESENT_STATES if state in _PRESENT_STATES else _ABSENT_STATES
    return sorted(
        {
            c.get(return_value)
            for c in data
            if isinstance(c, dict)
            and c.get("state") in state_filter
            and c.get(return_value)
        }
    )


class FilterModule:
    def filters(self):
        return {"container_state": container_state}
