#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

"""
Base helper class for Ansible container-related Jinja2 filters.

This class consolidates commonly used utility methods for container
filter modules such as key extraction, dictionary merging, and cleanup.
It ensures type-safety, consistent error handling, and Ansible-style
verbose logging via ansible.utils.display.Display.

Other filter modules (e.g., ContainerFilters, MountFilters, ReportingFilters)
should inherit from ContainerBase to reuse these methods consistently.
"""

import itertools
from typing import Any, Dict, List, Optional, Union

from ansible.utils.display import Display

display = Display()


class ContainerBase:
    """Base helper class providing reusable methods for container-related filters."""

    def _get_keys_from_dict(
        self, dictionary: List[Dict[str, Any]], key: str
    ) -> List[Any]:
        """
        Extract all values for a given key from a list of dictionaries.

        Args:
            dictionary (list): List of dictionaries to search.
            key (str): Key to extract values for.

        Returns:
            list: List of extracted values corresponding to the provided key.
        """
        display.vv(f"ContainerBase::_get_keys_from_dict({dictionary}, {key})")

        result: List[Any] = []
        for item in dictionary:
            if isinstance(item, dict):
                value = item.get(key)
                if value is not None:
                    result.append(value)
        return result

    def _del_keys_from_dict(
        self, dictionary: List[Dict[str, Any]], key: str
    ) -> List[Dict[str, Any]]:
        """
        Remove a specific key from all dictionaries in a list.

        Args:
            dictionary (list): List of dictionaries to modify.
            key (str): Key to remove from each dictionary.

        Returns:
            list: Modified list with the specified key removed.
        """
        display.vv(f"ContainerBase::_del_keys_from_dict({dictionary}, {key})")

        for item in dictionary:
            if isinstance(item, dict):
                item.pop(key, None)
        return dictionary

    def _safe_merge(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge two dictionaries safely and remove falsy values.

        Args:
            base (dict): Base dictionary.
            override (dict): Dictionary with override values.

        Returns:
            dict: Merged dictionary with falsy values (None, '', False) removed.
        """
        display.vv(f"ContainerBase::_safe_merge({base}, {override})")

        merged = {**base, **override}
        cleaned = {k: v for k, v in merged.items() if v not in (None, "", False)}
        return cleaned

    def _flatten_list(self, data: List[Any]) -> List[Any]:
        """
        Flatten a list of lists into a single list.

        Args:
            data (list): Nested list of arbitrary depth.

        Returns:
            list: Flattened list.
        """
        display.vv(f"ContainerBase::_flatten_list({data})")

        try:
            return list(itertools.chain.from_iterable(data))
        except TypeError:
            # In case elements are not iterable, just return the input
            return data

    def _validate_dict_key(self, data: Dict[str, Any], key: str) -> Optional[Any]:
        """
        Validate that a key exists in a dictionary and return its value.

        Args:
            data (dict): Dictionary to inspect.
            key (str): Key to check.

        Returns:
            Any or None: Value associated with the key if it exists, otherwise None.
        """
        display.vv(f"ContainerBase::_validate_dict_key({data}, {key})")

        if not isinstance(data, dict):
            display.v(
                f"ContainerBase::_validate_dict_key: Expected dict, got {type(data).__name__}"
            )
            return None

        if key not in data:
            display.v(
                f"ContainerBase::_validate_dict_key: Key '{key}' not found in {data}"
            )
            return None

        return data.get(key)
