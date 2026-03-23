#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ansible.errors import AnsibleFilterError
from ansible.utils.display import Display

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
  name: combine_registries
  short_description: Merge user-provided registry configurations with default values.
  version_added: "1.0.0"
  author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
  description:
    - Combines either a single registry definition or a list of registries with
      a set of default settings.
    - Falsy values (C(None), empty strings, C(False)) are stripped from the result.
  positional: _input, defaults
  options:
    _input:
      description: User-defined registry configuration(s) as a dict or list of dicts.
      type: raw
      required: true
    defaults:
      description: A list containing at least one default registry configuration dictionary.
      type: list
      elements: dict
      required: true
"""

EXAMPLES = r"""
- name: Merge user registries with defaults
  ansible.builtin.debug:
    msg: "{{ user_registries | bodsch.docker.combine_registries([default_registry]) }}"
"""

RETURN = r"""
  _value:
    description: List of merged and cleaned registry configuration dictionaries.
    type: list
    elements: dict
"""

# ---------------------------------------------------------------------------------------


display = Display()


def _safe_merge(base, override):
    merged = {**base, **override}
    return {k: v for k, v in merged.items() if v not in (None, "", False)}


def combine_registries(data, defaults):
    """Merge user-provided registry configurations with default values."""
    display.vv(f"combine_registries({data}, {defaults})")
    if not defaults:
        raise AnsibleFilterError(
            "combine_registries: requires at least one default configuration."
        )
    _default = defaults[0].copy()
    result = []
    if isinstance(data, dict):
        result.append(_safe_merge(_default, data))
    elif isinstance(data, list):
        for entry in data:
            if not isinstance(entry, dict):
                continue
            result.append(_safe_merge(_default, entry))
    return result


class FilterModule:
    def filters(self):
        return {"combine_registries": combine_registries}
