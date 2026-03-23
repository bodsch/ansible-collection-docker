#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import itertools

from ansible.utils.display import Display

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
  name: container_filter
  short_description: Aggregate container information for specific states.
  version_added: "1.0.0"
  author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
  description:
    - Builds a summary dictionary of container attributes (names, images, mounts,
      volumes, environments) for all containers in the input list.
    - Optionally excludes containers whose state matches entries in C(ignore_states).
  positional: _input, ignore_states
  options:
    _input:
      description: List of container definition dictionaries.
      type: list
      elements: dict
      required: true
    ignore_states:
      description: List of states to exclude from the C(launch) result (e.g. C(["present"])).
      type: list
      elements: str
      required: false
"""

EXAMPLES = r"""
- name: Aggregate container info excluding present state
  ansible.builtin.debug:
    msg: "{{ containers | bodsch.docker.container_filter(['present']) }}"
"""

RETURN = r"""
  _value:
    description: >
      Dictionary with keys: names, images, launch, mounts, volumes, environnments.
    type: dict
"""

# ---------------------------------------------------------------------------------------


display = Display()


# ---------------------------------------------------------------------------
# Inline helpers (no cross-file imports needed in standalone filter files)
# ---------------------------------------------------------------------------


def _container_names(data):
    return [c.get("name") for c in data if "name" in c]


def _container_images(data):
    return [c.get("image") for c in data if "image" in c]


def _container_ignore_state(data, ignore_states):
    return [i for i in data if i.get("state", "started") not in ignore_states]


def _container_volumes(data):
    result = []
    for container in data:
        for entry in container.get("volumes", []):
            if not isinstance(entry, str):
                continue
            values = entry.split(":")
            if len(values) >= 2:
                result.append({"local": values[0], "remote": values[1]})
    return result


def _container_mounts(data):
    result = []
    raw = [
        item.get("mounts")
        for item in data
        if isinstance(item, dict) and item.get("mounts") is not None
    ]
    merged = list(itertools.chain.from_iterable(raw))
    for item in merged:
        if not isinstance(item, dict):
            continue
        source_handling = item.get("source_handling", {})
        if isinstance(source_handling, dict) and source_handling.get("create", False):
            result.append(item)
    return result


def _container_environnments(data, want_list=None):
    if want_list is None:
        want_list = [
            "name",
            "hostname",
            "environments",
            "properties",
            "property_files",
            "config_files",
        ]
    return [{k: v for k, v in item.items() if k in want_list} for item in data]


# ---------------------------------------------------------------------------


def container_filter(data, ignore_states=None):
    """Aggregate container information, optionally excluding specific states."""
    display.vv(f"container_filter(data, ignore_states={ignore_states})")

    if ignore_states is None:
        ignore_states = []

    launch = (
        _container_ignore_state(data, ignore_states) if ignore_states else list(data)
    )

    return {
        "names": _container_names(data),
        "images": _container_images(data),
        "launch": launch,
        "mounts": _container_mounts(data),
        "volumes": _container_volumes(data),
        "environnments": _container_environnments(data),
    }


class FilterModule:
    def filters(self):
        return {"container_filter": container_filter}
