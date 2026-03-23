#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ansible.errors import AnsibleFilterError
from ansible.utils.display import Display

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
  name: reporting
  short_description: Create a filtered report of changed or failed containers.
  version_added: "1.0.0"
  author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
  description:
    - Filters a list of Ansible task results and returns either the names of changed
      containers or a list of error dictionaries for failed containers.
    - For C(report_for=changed), returns a list of hostnames, names, or image identifiers.
    - For C(report_for=failed), returns a list of dicts mapping the identifier to the error message.
  positional: _input, report_for
  options:
    _input:
      description: A dict with a C(results) key or a flat list of Ansible task result dictionaries.
      type: raw
      required: true
    report_for:
      description: Whether to report on C(changed) or C(failed) containers.
      type: str
      choices: [changed, failed]
      required: true
"""

EXAMPLES = r"""
- name: Report changed containers
  ansible.builtin.debug:
    msg: "{{ container_results | bodsch.docker.reporting('changed') }}"

- name: Report failed containers
  ansible.builtin.debug:
    msg: "{{ container_results | bodsch.docker.reporting('failed') }}"
"""

RETURN = r"""
  _value:
    description: >
      For changed: list of name/hostname/image strings.
      For failed: list of dicts mapping identifier to error message.
    type: list
"""

# ---------------------------------------------------------------------------------------


display = Display()


def reporting(data, report_for):
    """Create a filtered report of changed or failed containers."""
    display.vv(f"reporting(data, {report_for})")

    if isinstance(data, dict):
        results = data.get("results", [])
    elif isinstance(data, list):
        results = data
    else:
        raise AnsibleFilterError(
            "reporting: invalid data structure, expected dict or list."
        )

    states = [
        entry
        for entry in results
        if isinstance(entry, dict) and entry.get(report_for, False)
    ]

    result = []
    for item in states:
        container_data = item.get("item", {})
        name = container_data.get("name")
        hostname = container_data.get("hostname")
        image = container_data.get("image")
        msg = item.get("msg")
        identifier = hostname or name or image

        if not identifier:
            continue

        if report_for == "changed":
            result.append(identifier)
        elif report_for == "failed":
            result.append({identifier: msg})

    return result


class FilterModule:
    def filters(self):
        return {"reporting": reporting}
