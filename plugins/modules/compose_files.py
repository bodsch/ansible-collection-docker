#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2023, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function
import os

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.directory import create_directory, current_state
from ansible_collections.bodsch.core.plugins.module_utils.lists import compare_two_lists

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


class ComposeFiles(object):
    """
    """

    def __init__(self, module):
        """
        """
        self.module = module

    def run(self):
        """
        """
        result = dict(
            changed=False,
            failed=True,
            msg="initial"
        )

# ---------------------------------------------------------------------------------------


def main():
    """
    """
    args = dict(
        base_directory = dict(
            required=True,
            type='str'
        ),
        version=dict(
            required=False,
            type='str'
        ),
        networks=dict(
            required=False,
            type='list'
        ),
        services=dict(
            required=False,
            type='list'
        )
    )

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=True,
    )

    p = ComposeFiles(module)
    result = p.run()

    module.log(msg=f"= result: {result}")
    module.exit_json(**result)


if __name__ == '__main__':
    main()
