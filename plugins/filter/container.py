#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

"""
Unified Ansible filter plugin for container-related Jinja2 filters.

This file exposes all container filters (split across multiple modules)
as a single Ansible filter plugin called 'container'.
"""

from typing import Any, Dict

from ansible.utils.display import Display

# Import all filter classes
from .container_pkg.container_filters import ContainerFilters
from .container_pkg.helpers_filters import HelpersFilters
from .container_pkg.mount_filters import MountFilters
from .container_pkg.registry_filters import RegistryFilters
from .container_pkg.reporting_filters import ReportingFilters

display = Display()


class FilterModule(
    ContainerFilters,
    # EnvironmentFilters,
    MountFilters,
    RegistryFilters,
    ReportingFilters,
    HelpersFilters,
):
    """
    Unified filter plugin that exposes all container-related filters.

    This class aggregates multiple specialized filter modules into a single
    Ansible filter plugin under the name ``container``.
    """

    def filters(self) -> Dict[str, Any]:
        """
        Merge and return all filters from submodules.

        Iterates over the inheritance tree (MRO) and collects filters
        registered by each mixin class.

        Returns:
            dict: Combined dictionary of all available filter functions.
        """
        display.vv("FilterModule::filters()")
        all_filters = {}

        # Traverse MRO, merging sub-filter dictionaries
        for cls in self.__class__.__mro__:
            if hasattr(cls, "filters") and cls is not FilterModule:
                try:
                    all_filters.update(cls.filters(self))  # type: ignore
                except Exception as e:
                    display.v(
                        f"Warning: could not load filters from {cls.__name__}: {e}"
                    )

        return all_filters

    # def _get_keys_from_dict(
    #     self, dictionary: List[Dict[str, Any]], key: str
    # ) -> List[Any]:
    #     """
    #     Helper method to extract values for a given key from a list of dictionaries.
    #
    #     Args:
    #         dictionary (list): List of dictionaries to search.
    #         key (str): Key to extract values for.
    #
    #     Returns:
    #         list: List of extracted values for the given key.
    #     """
    #     display.vv(f"FilterModule::_get_keys_from_dict({dictionary}, {key})")
    #
    #     result: List[Any] = []
    #     for item in dictionary:
    #         if isinstance(item, dict):
    #             value = item.get(key)
    #             if value is not None:
    #                 result.append(value)
    #
    #     return result
    #
    # def _del_keys_from_dict(
    #     self, dictionary: List[Dict[str, Any]], key: str
    # ) -> List[Dict[str, Any]]:
    #     """
    #     Remove a specific key from all dictionaries in a list.
    #
    #     Args:
    #         dictionary (list): List of dictionaries to modify.
    #         key (str): Key to remove from each dictionary.
    #
    #     Returns:
    #         list: The modified list with the specified key removed.
    #     """
    #     display.vv(f"FilterModule::_del_keys_from_dict({dictionary}, {key})")
    #
    #     for item in dictionary:
    #         if isinstance(item, dict):
    #             item.pop(key, None)
    #
    #     return dictionary
    #
    # def _safe_merge(self, a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    #     """
    #     Merge two dictionaries safely and return a cleaned copy.
    #
    #     None or empty values are removed from the resulting dictionary.
    #
    #     Args:
    #         a (dict): Base dictionary.
    #         b (dict): Dictionary with overrides.
    #
    #     Returns:
    #         dict: Merged dictionary with falsy values removed.
    #     """
    #     display.vv(f"FilterModule::_safe_merge({a}, {b})")
    #
    #     merged = {**a, **b}
    #     return {k: v for k, v in merged.items() if v}
    #
