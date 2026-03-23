#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ansible.utils.display import Display

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
  name: container_ignore_state
  short_description: Filter out containers with specific states.
  version_added: "1.0.0"
  author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
  description:
    - Returns only those container definitions whose C(state) is NOT in the
      C(ignore_states) list.
    - Containers without an explicit C(state) key are treated as having state C(started).
    - Defaults to filtering out containers with state C(present).
  positional: _input, ignore_states
  options:
    _input:
      description: List of container definition dictionaries.
      type: list
      elements: dict
      required: true
    ignore_states:
      description: List of states to exclude. Defaults to C(["present"]).
      type: list
      elements: str
      required: false
"""

EXAMPLES = r"""
- name: Exclude containers with state=present
  ansible.builtin.debug:
    msg: "{{ containers | bodsch.docker.container_ignore_state(['present']) }}"
"""

RETURN = r"""
  _value:
    description: List of container definitions not matching any ignored state.
    type: list
    elements: dict
"""

# ---------------------------------------------------------------------------------------


display = Display()


def container_ignore_state(data, ignore_states=None):
    """Filter out containers whose state is in ignore_states."""
    if ignore_states is None:
        ignore_states = ["present"]

    display.vv(f"container_ignore_state(data, {ignore_states})")

    ignored = [i for i in data if i.get("state", "started") in ignore_states]
    result = [i for i in data if i.get("state", "started") not in ignore_states]

    display.vv(f"  ignore: {[i.get('name') for i in ignored]}")
    display.vv(f"  launch: {[i.get('name') for i in result]}")

    return result


class FilterModule:
    def filters(self):
        return {"container_ignore_state": container_ignore_state}
