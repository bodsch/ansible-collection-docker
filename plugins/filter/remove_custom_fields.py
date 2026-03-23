#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ansible.utils.display import Display

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
  name: remove_custom_fields
  short_description: Remove custom field metadata from string entries.
  version_added: "1.0.0"
  author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
  description:
    - Strips additional metadata appended to strings with a C(|) separator.
    - Returns only the base value before the separator.
    - Accepts either a single string or a list of strings.
  positional: _input
  options:
    _input:
      description: A single string or a list of strings potentially containing C(|)-separated metadata.
      type: raw
      required: true
"""

EXAMPLES = r"""
- name: Strip custom metadata from strings
  ansible.builtin.debug:
    msg: "{{ volume_list | bodsch.docker.remove_custom_fields }}"
"""

RETURN = r"""
  _value:
    description: Cleaned string or list of strings without custom metadata.
    type: raw
"""

# ---------------------------------------------------------------------------------------


display = Display()


def remove_custom_fields(data):
    """Remove custom field information (after '|') from string entries."""
    display.vv(f"remove_custom_fields({data})")
    if isinstance(data, list):
        return [v.split("|")[0] for v in data if isinstance(v, str)]
    return data


class FilterModule:
    def filters(self):
        return {"remove_custom_fields": remove_custom_fields}
