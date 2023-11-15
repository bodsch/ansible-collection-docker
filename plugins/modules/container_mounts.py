#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2021-2023, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

from ansible.module_utils.basic import AnsibleModule
from ruamel.yaml import YAML
from ansible_collections.bodsch.core.plugins.module_utils.lists import compare_two_lists
from ansible_collections.bodsch.core.plugins.module_utils.directory import create_directory_tree, current_state

# ---------------------------------------------------------------------------------------

DOCUMENTATION = """
module: container_mounts
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

class ContainerMounts(object):
    """
    """

    def __init__(self, module):
        """
        """
        self.module = module

        self.data = module.params.get("data")
        self.volumes = module.params.get("volumes")
        self.mounts = module.params.get("mounts")
        self.debug = module.params.get("debug")
        self.owner = module.params.get("owner")
        self.group = module.params.get("group")
        self.mode = module.params.get("mode")

        self.volume_block_list_ends = (
            '.pid',
            '.sock',
            '.socket',
            '.conf',
            '.config',
        )
        self.volume_block_list_starts = (
            '/sys',
            '/dev',
            '/run',
        )

        self.read_only = {
            'rw': False,
            'ro': True
        }

    def run(self):
        """
        """
        result = dict(
            changed=False,
            failed=True,
            msg="initial"
        )

        all_mounts = []
        all_volumes = []
        migrated_volumes = []

        if self.volumes:
            all_volumes = self.__volumes()
            migrated_volumes = self.__migrate_volumes_to_mounts(all_volumes)

        if self.mounts:
            all_mounts = self.__mounts()

        full_list = migrated_volumes + all_mounts

        if len(full_list) == 0:
            return dict(
                changed=False,
                failed=False,
                msg="nothing to do"
            )

        current_state = self.__analyse_directories(full_list)
        create_directory_tree(full_list, current_state)
        final_state = self.__analyse_directories(full_list)

        changed, diff, error_msg = compare_two_lists(list1=current_state, list2=final_state)

        # self.module.log(f"   changed: {changed}, diff: {diff}")

        # TODO
        # remove custom fields from 'volumes'
        if changed:
            result['msg'] = "changed or created directories"
            msg = ""
            for i in diff:
                msg += f"- {i}\n"
            result['created_directories'] = msg
        else:
            result['msg'] = "nothing to do"

        result['changed'] = changed
        result['failed'] = False

        return result

    def __volumes(self):
        """
          return all volume definitions
        """
        all_volumes = []

        for d in self.data:
            _v = d.get('volumes', [])
            if len(_v) > 0:
                all_volumes.append(_v)

        return all_volumes

    def __mounts(self):
        """
          get only mountspoint when we add source_handling and set create to True
        """
        all_mounts = []

        for d in self.data:
            """
            """
            if self.debug:
                self.module.log(f"- {d.get('name')}")

            mount_defintions = d.get('mounts', [])

            for mount in mount_defintions:
                if self.debug:
                    self.module.log(f"  mount: {mount}")

                source_handling = mount.get('source_handling', {}).get("create", False)

                if len(mount_defintions) > 0 and source_handling:
                    all_mounts.append(mount)

        return all_mounts

    def __migrate_volumes_to_mounts(self, volumes):
        """
            migrate old volume definition into mount
            ignore some definitions like:
              - *.sock
              - *.conf
            etc. see self.volume_block_list_ends and self.volume_block_list_starts!

            for example:
              from: /tmp/testing5:/var/tmp/testing5|{owner="1001",mode="0700",ignore=True}
              to:
              - source: /tmp/testing5
                target: /var/tmp/testing5
                source_handling:
                  create: false
                  owner: "1001"
                  mode: "0700"

              from: /tmp/testing3:/var/tmp/testing3:rw|{owner="999",group="1000"}
              to:
              - source: /tmp/testing3
                target: /var/tmp/testing3
                source_handling:
                  create: true
                  owner: "999"
                  group: "1000"
        """
        if self.debug:
            self.module.log("__migrate_volumes_to_mounts(volumes)")

        result = []
        yaml = YAML()

        def custom_fields(d):
            """
              returns only custom fileds as json
            """
            d = d.replace('=', ': ')

            if d.startswith("[") and d.endswith("]"):
                d = d.replace("[", "")
                d = d.replace("]", "")

            if not (d.startswith("{") and d.endswith("}")):
                d = "{" + d + "}"

            code = yaml.load(d)

            for key, value in code.items():
                # transform ignore=True into create=False
                if key == "ignore":
                    code.insert(0, 'create', not value)
                    del code[key]

            if self.debug:
                self.module.log(f"    custom_fields: {dict(code)}")

            return dict(code)

        for d in volumes:
            for entry in d:
                """
                """
                if self.debug:
                    self.module.log(f"  - {entry}")

                read_mode = None
                c_fields = dict()
                values = entry.split('|')

                if len(values) == 2 and values[1]:
                    c_fields = custom_fields(values[1])
                    entry = values[0]

                values = entry.split(':')
                count = len(values)

                local_volume = values[0]
                remote_volume = values[1]

                if count == 3 and values[2]:
                    read_mode = values[2]

                valid = (local_volume.endswith(self.volume_block_list_ends) or local_volume.startswith(
                    self.volume_block_list_starts))

                if not valid:
                    """
                    """
                    res = dict(
                        source=local_volume,   # values[0],
                        target=remote_volume,  # values[1],
                        type="bind",
                        source_handling=c_fields
                    )

                    if read_mode is not None:
                        res['read_only'] = self.read_only.get(read_mode)

                    result.append(res)

        return result

    def __analyse_directories(self, directory_tree):
        """
          set current owner, group and mode to source entry
        """
        result = []
        for entry in directory_tree:
            """
            """
            res = {}

            source = entry.get('source')
            current_owner = None
            current_group = None
            current_mode = None

            res[source] = {}

            current_owner, current_group, current_mode = current_state(source)

            res[source].update({
                "owner": current_owner,
                "group": current_group,
                "mode": current_mode,
            })

            result.append(res)

        return result


# ===========================================
# Module execution.

def main():
    """
    """
    args = dict(
        data=dict(
            required=True,
            type='list'
        ),
        volumes=dict(
            required=True,
            type='bool'
        ),
        mounts=dict(
            required=True,
            type='bool'
        ),
        debug=dict(
            required=False,
            default=False,
            type='bool'
        ),
        owner=dict(
            required=False
        ),
        group=dict(
            required=False
        ),
        mode=dict(
            required=False,
            type="str"
        ),
    )

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=True,
    )

    p = ContainerMounts(module)
    result = p.run()

    module.log(msg=f"= result: {result}")
    module.exit_json(**result)


if __name__ == '__main__':
    main()
