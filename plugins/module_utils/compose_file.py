#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2020-2023, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

# import os
# import yaml
import ruamel.yaml

from ansible_collections.bodsch.core.plugins.module_utils.checksum import Checksum


class ComposeFile:
    """
    """

    def __init__(self, module):
        self.module = module

    def create(self, version=None, networks={}, services={}):
        """
        """
        # self.module.log(msg=f"ComposeFile::create()")

        result = dict()

        if version:
            result["version"] = version

        if networks:
            result["networks"] = networks

        if services:
            result["services"] = services

        return result

    def write(self, file_name, data):
        """
        """
        yaml = ruamel.yaml.YAML()
        yaml.indent(sequence=4, offset=2)
        # yaml.dump(data, f)

        with open(file_name, "w") as f:
            yaml.dump(data, f)
            # yaml.dump(data, f, sort_keys=False)

    def validate(self, tmp_file, data_file):
        """
        """
        checksum = Checksum(self.module)

        new_checksum = checksum.checksum_from_file(tmp_file)
        old_checksum = checksum.checksum_from_file(data_file)

        changed = not (new_checksum == old_checksum)

        return changed
