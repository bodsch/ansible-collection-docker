#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2023, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function
import os
# import shutils

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.directory import create_directory
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


class ModuleComposeFiles(object):
    """
    """

    def __init__(self, module):
        """
        """
        self.module = module

        self.base_directory = module.params.get("base_directory")
        # self.compose_filename = module.params.get("name")
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

        create_directory(directory=self.tmp_directory, mode="0750")

        if not os.path.isdir(self.base_directory):
            create_directory(directory=self.base_directory, mode="0755")

        self.composeFile = ComposeFile(self.module)

        self._save_networks()
        self._save_services()

        return result

    def _save_networks(self):
        """
        """
        for net in self.networks:
            network_name = net.get("name", None)
            network_state = net.get("state", "present")

            if not network_name:
                """
                """
                continue

            self.module.log(msg=f"networks : {net}")

            file_name = os.path.join(self.base_directory, f"{network_name}.conf")

            if network_state == "absent":
                self.__file_state_absent(network_name, file_name)

            if network_state == "present":

                net.pop("name")
                net.pop("state")
                network = dict()
                network[network_name] = net

                self.__file_state_present(network_name, file_name, compose_type="networks", data=network)

    def _save_services(self):
        """
        """
        for svc in self.services:
            service_name = svc.get("name", None)
            service_state = svc.get("state", "present")

            self.module.log(msg=f"service : {service_name}.conf = {service_state}")

            if not service_name:
                """
                """
                continue

            file_name = os.path.join(self.base_directory, f"{service_name}.conf")

            if service_state == "absent":
                self.__file_state_absent(service_name, file_name)

            if service_state == "present":

                svc.pop("name")
                svc.pop("state")
                service = dict()
                service[service_name] = svc

                self.__file_state_present(service_name, file_name, compose_type="services", data=service)

    def __file_state_absent(self, service_name, file_name):
        """
        """
        if os.path.exists(file_name):
            _msg = f"The compose file ‘{service_name}.conf’ was successfully deleted."
            _changed = True
            os.remove(file_name)
        else:
            _msg = f"The compose file ‘{service_name}.conf’ has already been deleted."
            _changed = False

        return dict(
            changed=_changed,
            failed=False,
            msg=_msg
        )

    def __file_state_present(self, service_name=None, file_name=None, compose_type="services", data={}):
        """
        """
        self.module.log(msg=f"service : {service_name}")
        # self.module.log(msg=f"          {service}")

        if compose_type == "services":
            compose_data = self.composeFile.create(self.version, None, data)
        if compose_type == "networks":
            compose_data = self.composeFile.create(self.version, data, None)

        self.module.log(msg=f"          {compose_data}")

        tmp_file_name = os.path.join(self.tmp_directory, f"{service_name}.conf")

        self.composeFile.write(tmp_file_name, compose_data)


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

    p = ModuleComposeFiles(module)
    result = p.run()

    module.log(msg=f"= result: {result}")
    module.exit_json(**result)


if __name__ == '__main__':
    main()
