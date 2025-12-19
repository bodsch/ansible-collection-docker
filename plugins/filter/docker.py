#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright (c) 2021-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, print_function

from typing import Any, Dict, Optional

from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """
    Ansible filter plugin for validating Docker log driver configurations.

    This filter ensures that the provided log driver is either one of Docker's
    built-in drivers or follows the correct custom driver format: ``driver:version``.
    """

    def filters(self) -> Dict[str, Any]:
        """
        Register available Jinja2 filters.

        Returns:
            dict: Mapping of filter names to callable methods.
        """
        return {
            "validate_log_driver": self.validate_log_driver,
        }

    def validate_log_driver(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the format and value of a Docker log driver configuration.

        This filter checks whether the specified log driver is a recognized
        built-in driver or a correctly formatted custom plugin reference.

        Args:
            data (dict): Dictionary containing a ``log_driver`` key to validate.

        Returns:
            dict: Result dictionary with:
                - ``valid`` (bool): True if the driver is valid, otherwise False.
                - ``msg`` (str): A descriptive message indicating validation result.
        """
        display.vv(f"FilterModule::validate_log_driver({data})")

        built_in_drivers: list[str] = [
            "awslogs",
            "fluentd",
            "gcplogs",
            "gelf",
            "journald",
            "json-file",
            "local",
            "logentries",
            "splunk",
            "syslog",
        ]

        log_driver: Optional[str] = data.get("log_driver")

        if log_driver and log_driver not in built_in_drivers:
            # Custom plugin validation
            if ":" not in log_driver:
                return {
                    "valid": False,
                    "msg": (
                        "Invalid custom log driver format!\n"
                        "Expected format: <driver_name>:<driver_version>"
                    ),
                }

            _, plugin_version = log_driver.split(":", 1)

            if not plugin_version.strip():
                return {
                    "valid": False,
                    "msg": (
                        "Missing plugin version!\n"
                        "Expected format: <driver_name>:<driver_version>"
                    ),
                }

        return {"valid": True, "msg": "valid"}
