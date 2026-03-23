#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ansible.utils.display import Display

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
  name: remove_source_handling
  short_description: Remove the source_handling key from dictionaries.
  version_added: "1.0.0"
  author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
  description:
    - Removes the C(source_handling) key from a single dictionary or all dictionaries in a list.
    - Useful for cleaning container definitions before passing them to Docker modules.
  positional: _input
  options:
    _input:
      description: A dict or list of dicts potentially containing the C(source_handling) key.
      type: raw
      required: true
"""

EXAMPLES = r"""
- name: Strip source_handling before passing to docker module
  ansible.builtin.debug:
    msg: "{{ containers | bodsch.docker.remove_source_handling }}"
"""

RETURN = r"""
  _value:
    description: Input structure with the source_handling key removed.
    type: raw
"""

# ---------------------------------------------------------------------------------------


display = Display()


def remove_source_handling(data):
    """Remove 'source_handling' key from dicts or lists of dicts."""
    display.vv(f"remove_source_handling({data})")
    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict):
                entry.pop("source_handling", None)
        return data
    elif isinstance(data, dict):
        data.pop("source_handling", None)
    return data


class FilterModule:
    def filters(self):
        return {"remove_source_handling": remove_source_handling}
