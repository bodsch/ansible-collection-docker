#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2021-2023, Bodo Schulz <bodo@boone-schulz.de>
# Apache-2.0 (see LICENSE or https://opensource.org/license/apache-2-0)
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function
import os
import shutil

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.directory import create_directory
from ansible_collections.bodsch.core.plugins.module_utils.module_results import results
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

        self.tmp_directory = os.path.join("/run/.ansible", f"compose_files.{str(pid)}")

    def run(self):
        """
        """
        create_directory(directory=self.tmp_directory, mode="0750")

        if not os.path.isdir(self.base_directory):
            create_directory(directory=self.base_directory, mode="0755")

        self.composeFile = ComposeFile(self.module)

        network_result = self._save_networks()
        service_result = self._save_services()

        network_changed = network_result.get("changed")
        service_changed = service_result.get("changed")

        _changed = (network_changed or service_changed)

        shutil.rmtree(self.tmp_directory)

        return dict(
            changed = _changed,
            failed = False,
            networks = network_result,
            services = service_result
        )

    def _save_networks(self):
        """
        """
        result_state = []

        for net in self.networks:
            network_name = net.get("name", None)
            network_state = net.get("state", "present")

            if not network_name:
                """
                """
                continue

            network_res = {}

            file_name = os.path.join(self.base_directory, f"{network_name}.conf")

            if network_state == "absent":
                network_res[network_name] = self.__file_state_absent(network_name, file_name)

            if network_state == "present":
                net.pop("name")
                net.pop("state")
                network = dict()
                network[network_name] = net

                network_res[network_name] = self.__file_state_present(network_name, file_name, compose_type="networks", data=network)

            result_state.append(network_res)

        _state, _changed, _failed, state, changed, failed = results(self.module, result_state)

        result = dict(
            changed = _changed,
            failed = _failed,
            msg = result_state
        )

        return result

    def _save_services(self):
        """
        """
        result_state = []

        for svc in self.services:
            service_name = svc.get("name", None)
            service_state = svc.get("state", "present")

            if not service_name:
                """
                """
                continue

            service_res = {}

            file_name = os.path.join(self.base_directory, f"{service_name}.conf")

            if service_state == "absent":
                service_res[service_name] = self.__file_state_absent(service_name, file_name)

            if service_state == "present":

                svc.pop("name")
                if svc.get("state", None):
                    svc.pop("state")
                service = dict()
                service[service_name] = svc

                service_res[service_name] = self.__file_state_present(service_name, file_name, compose_type="services", data=service)

            result_state.append(service_res)

        _state, _changed, _failed, state, changed, failed = results(self.module, result_state)

        result = dict(
            changed = _changed,
            failed = _failed,
            msg = result_state
        )

        return result

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
        if compose_type == "services":
            compose_data = self.composeFile.create(self.version, None, data)
        if compose_type == "networks":
            compose_data = self.composeFile.create(self.version, data, None)

        tmp_file_name = os.path.join(self.tmp_directory, f"{service_name}.conf")

        self.composeFile.write(tmp_file_name, compose_data)

        _changed = self.composeFile.validate(tmp_file_name, file_name)

        if _changed:
            shutil.move(tmp_file_name, file_name)
            _msg = f"The compose file ‘{service_name}.conf’ was successful written."
        else:
            _msg = f"The compose file ‘{service_name}.conf’ has not been changed."

        return dict(
            changed=_changed,
            failed=False,
            msg=_msg
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

    p = ModuleComposeFiles(module)
    result = p.run()

    module.log(msg=f"= result: {result}")
    module.exit_json(**result)


if __name__ == '__main__':
    main()
