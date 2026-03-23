#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ansible.utils.display import Display

# ---------------------------------------------------------------------------------------

DOCUMENTATION = r"""
  name: container_images
  short_description: Return all container image names.
  version_added: "1.0.0"
  author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"
  description:
    - Extracts the C(image) field from each container definition in the input list.
  positional: _input
  options:
    _input:
      description: List of container definition dictionaries.
      type: list
      elements: dict
      required: true
"""

EXAMPLES = r"""
- name: Get all container images
  ansible.builtin.debug:
    msg: "{{ containers | bodsch.docker.container_images }}"
"""

RETURN = r"""
  _value:
    description: List of container image name strings.
    type: list
    elements: str
"""

# ---------------------------------------------------------------------------------------


display = Display()


def container_images(data):
    """Return all container image names."""
    display.vv(f"container_images({data})")
    return [c.get("image") for c in data if "image" in c]


class FilterModule:
    def filters(self):
        return {"container_images": container_images}
