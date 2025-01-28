#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2023, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function
import os

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.directory import create_directory, current_state
from ansible_collections.bodsch.core.plugins.module_utils.checksum import Checksum
# from ansible_collections.bodsch.core.plugins.module_utils.lists import compare_two_lists
from ansible_collections.bodsch.docker.plugins.module_utils.compose_file import ComposeFile

# ---------------------------------------------------------------------------------------

DOCUMENTATION = """
module: compose_files
version_added: 1.0.0
author: "Bodo Schulz (@bodsch) <bodo@boone-schulz.de>"

short_description: TBD

description:
    - TBD
"""

EXAMPLES = """
"""

RETURN = """
"""

# ---------------------------------------------------------------------------------------


class ComposeFile(object):
    """
    """
    def __init__(self, module):
        """
        """
        self.module = module

        self.base_directory = module.params.get("base_directory")
        self.compose_filename = module.params.get("name")
        self.version = module.params.get("version")
        self.networks = module.params.get("networks")
        self.services = module.params.get("services")

        pid = os.getpid()

        self.tmp_directory = os.path.join("/run/.ansible", f"compose_file.{str(pid)}")

    def run(self):
        """
        """
        result = dict(
            changed=False,
            failed=True,
            msg="initial"
        )

        if not os.path.isdir(self.base_directory):
            create_directory(directory=self.base_directory, mode="0755")

        self.checksum = Checksum(self.module)


        return result

# ---------------------------------------------------------------------------------------

def main():
    """
    """
    args = dict(
        base_directory = dict(
            required=True,
            type='str'
        ),
        name = dict(
            required=True,
            type='str'
        ),
        version=dict(
            required=False,
            type='str'
        ),
        networks=dict(
            required=False,
            type='dict'
        ),
        services=dict(
            required=False,
            type='dict'
        )
    )

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=True,
    )

    p = ComposeFile(module)
    result = p.run()

    module.log(msg=f"= result: {result}")
    module.exit_json(**result)


if __name__ == '__main__':
    main()
