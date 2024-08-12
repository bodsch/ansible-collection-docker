#!/usr/bin/python3
# -*- coding: utf-8 -*-

# (c) 2020, Bodo Schulz <bodo@boone-schulz.de>
# BSD 2-clause (see LICENSE or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
import os
import json
import docker

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.directory import create_directory

__metaclass__ = type

# ---------------------------------------------------------------------------------------

DOCUMENTATION = """
module: docker_plugins
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


class DockerPlugins():
    """
      Main Class to implement the installation of docker plugins
    """
    module = None

    def __init__(self, module):
        """
          Initialize all needed Variables
        """
        self.module = module
        self.state = module.params.get("state")
        #
        self.plugin_source = module.params.get("plugin_source")
        self.plugin_version = module.params.get("plugin_version")
        self.plugin_alias = module.params.get("plugin_alias")
        self.docker_data_root = module.params.get("data_root")

        self.cache_directory = "/var/cache/ansible/docker"
        self.plugin_information_file = os.path.join(self.cache_directory, f"plugin_{self.plugin_alias}")

        self.docker_socket = "/var/run/docker.sock"

    def run(self):
        """
            run
        """
        docker_status = False
        # TODO
        # with broken ~/.docker/daemon.json will this fail!
        try:
            if os.path.exists(self.docker_socket):
                # self.module.log("use docker.sock")
                self.docker_client = docker.DockerClient(base_url=f"unix://{self.docker_socket}")
            else:
                self.docker_client = docker.from_env()

            docker_status = self.docker_client.ping()
            docker_info = self.docker_client.info()

            self.docker_current_data_root = docker_info.get('DockerRootDir', None)

        except docker.errors.APIError as e:
            self.module.log(
                msg=f" exception: {e}"
            )
        except Exception as e:
            self.module.log(
                msg=f" exception: {e}"
            )

        if not docker_status:
            return dict(
                changed = False,
                failed = True,
                msg = "no running docker found"
            )

        create_directory(self.cache_directory)

        self.plugin_state, plugin_id, self.plugin_version_equal, plugin_state_message = self.check_plugin()

        # self.module.log(msg=f"  plugin_state          : {self.plugin_state}")
        # self.module.log(msg=f"  plugin_version_equal  : {self.plugin_version_equal}")
        # self.module.log(msg=f"  plugin_state_message  : {plugin_state_message}")
        # self.module.log(msg=f"  data_root             : {self.docker_data_root}")
        # self.module.log(msg=f"  current_data_root     : {self.docker_current_data_root}")

        if self.state == "test":
            """
            """
            if plugin_id:
                plugin_config_file = os.path.join(self.docker_data_root, "plugins", plugin_id, "config.json")

                if not os.path.exists(plugin_config_file):
                    self.module.log(msg=f"The plugin {self.plugin_alias} is not installed under the expected data-root path {self.docker_data_root}.")

            return dict(
                changed = False,
                installed = self.plugin_state,
                equal_versions = self.plugin_version_equal,
                msg = plugin_state_message
            )

        if self.state == "absent":
            return self.uninstall_plugin()

        return self.install_plugin()

    def check_plugin(self):
        """
        """
        installed_plugin_enabled = False
        installed_plugin_name = None
        installed_plugin_shortname = None
        installed_plugin_version = None
        installed_plugin_id = None
        installed_plugin_short_id = None

        equal_versions = True

        msg = f"plugin {self.plugin_alias} ist not installed"

        try:
            p_list = self.docker_client.plugins.list()

            for plugin in p_list:
                installed_plugin_enabled = plugin.enabled
                installed_plugin_shortname = plugin.name.split(':')[0]

                if installed_plugin_shortname == self.plugin_alias:
                    installed_plugin_name = plugin.name
                    installed_plugin_shortname = plugin.name.split(':')[0]
                    installed_plugin_version = plugin.name.split(':')[1]
                    installed_plugin_id = plugin.id
                    installed_plugin_short_id = plugin.short_id

                    break

        except docker.errors.APIError as e:
            error = str(e)
            self.module.log(msg=f"{error}")

        except Exception as e:
            error = str(e)
            self.module.log(msg=f"{error}")

        # self.module.log(msg=f"  name     : {installed_plugin_name}")
        # self.module.log(msg=f"  shortname: {installed_plugin_shortname}")
        # self.module.log(msg=f"  version  : {installed_plugin_version}")
        # self.module.log(msg=f"  short_id : {installed_plugin_short_id}")
        # self.module.log(msg=f"  enabled  : {installed_plugin_enabled}")
        #
        # self.module.log(msg=f"  version wanted: {self.plugin_version}")

        self.installed_plugin_data = dict(
            id = installed_plugin_id,
            short_id = installed_plugin_short_id,
            name = installed_plugin_name,
            short_name = installed_plugin_shortname,
            version = installed_plugin_version,
            enabled = installed_plugin_enabled
        )

        if installed_plugin_name and installed_plugin_version:
            msg = f"plugin {installed_plugin_shortname} is installed in version '{installed_plugin_version}'"

            if self.plugin_version == installed_plugin_version:
                self.__write_plugin_information(self.installed_plugin_data)
            else:
                equal_versions = False
                msg += f", but versions are not equal! (your choise {self.plugin_version} vs. installed {installed_plugin_version})"

            return True, installed_plugin_id, equal_versions, msg
        else:
            return False, None, False, msg

    def plugin_information(self, plugin_data):
        """
        """
        self.module.log(msg=f"  name     : {plugin_data.name}")
        self.module.log(msg=f"    enabled  : {plugin_data.enabled}")
        self.module.log(msg=f"    shortname: {plugin_data.name.split(':')[0]}")
        self.module.log(msg=f"    version  : {plugin_data.name.split(':')[1]}")
        self.module.log(msg=f"    short_id : {plugin_data.short_id}")
        self.module.log(msg=f"    id       : {plugin_data.id}")

        self.module.log(msg=f"  version wanted: {self.plugin_version}")

    def install_plugin(self):
        """
        """
        installed_plugin = self.installed_plugin_data.get('name', None)

        if not self.plugin_version_equal and installed_plugin:
            """
                disable old plugin
            """
            self.module.log(msg=f"disable other plugin version ({installed_plugin})")
            try:
                installed_plugin = self.docker_client.plugins.get(f"{installed_plugin}")

                if installed_plugin:
                    installed_plugin.disable(force=True)

            except docker.errors.APIError as e:
                error = str(e)
                self.module.log(msg=f"{error}")

            except Exception as e:
                error = str(e)
                self.module.log(msg=f"{error}")

        self.module.log(msg=f"Check whether the plugin {self.plugin_alias} is already installed in version {self.plugin_version}")

        try:
            installed_plugin = self.docker_client.plugins.get(f"{self.plugin_alias}:{self.plugin_version}")

        except docker.errors.APIError as e:
            error = str(e)
            self.module.log(msg=f"{error}")
            installed_plugin = None
            pass

        if installed_plugin:

            # _installed_plugin = installed_plugin
            self.plugin_information(installed_plugin)

            # self.module.log(msg=f"{self.docker_data_root}")
            # self.module.log(msg=f"{str(installed_plugin.id)}")
            # self.module.log(msg=f"{installed_plugin.id}")

            plugin_config_file = os.path.join(self.docker_data_root, "plugins", installed_plugin.id, "config.json")

            # self.module.log(msg=f"{plugin_config_file}")

            if not os.path.exists(plugin_config_file):
                self.module.log(msg=f"The plugin {self.plugin_alias} is not installed under the expected data-root path {self.docker_data_root}.")
                self.uninstall_plugin()

            try:
                self.module.log(msg="re-enable plugin")
                installed_plugin.enable(timeout=10)
            except docker.errors.APIError as e:
                error = str(e)
                self.module.log(msg=f"{error}")
                pass

            try:
                self.module.log(msg="reload plugin attrs")
                installed_plugin.reload()
            except docker.errors.APIError as e:
                error = str(e)
                self.module.log(msg=f"{error}")
                pass

            result = dict(
                changed = True,
                failed = False,
                msg = f"plugin {self.plugin_alias} was successfully re-enabled in version {self.plugin_version}"
            )

        else:
            try:
                self.module.log(msg=f"install plugin in version {self.plugin_version}")

                plugin = self.docker_client.plugins.install(
                    remote_name=f"{self.plugin_source}:{self.plugin_version}",
                    local_name=f"{self.plugin_alias}:{self.plugin_version}")

                try:
                    self.module.log(msg="enable plugin")
                    plugin.enable(timeout=10)
                except docker.errors.APIError as e:
                    error = str(e)
                    self.module.log(msg=f"{error}")
                    pass

                try:
                    self.module.log(msg="reload plugin attrs")
                    plugin.reload()
                except docker.errors.APIError as e:
                    error = str(e)
                    self.module.log(msg=f"{error}")
                    pass

                installed_plugin_shortname = plugin.name.split(':')[0]
                installed_plugin_version = plugin.name.split(':')[1]

                result = dict(
                    changed = True,
                    failed = False,
                    msg = f"plugin {installed_plugin_shortname} was successfully installed in version {installed_plugin_version}"
                )

            except docker.errors.APIError as e:
                error = str(e)
                self.module.log(msg=f"{error}")

                result = dict(
                    changed = False,
                    failed = True,
                    msg = error
                )

            except Exception as e:
                error = str(e)
                self.module.log(msg=f"{error}")

                result = dict(
                    changed = False,
                    failed = True,
                    msg = error
                )

        return result

    def uninstall_plugin(self):
        """
        """
        installed_plugin = self.installed_plugin_data.get('name', None)

        if installed_plugin:
            """
                disable old plugin
            """
            try:
                installed_plugin = self.docker_client.plugins.get(f"{installed_plugin}")

                if installed_plugin:
                    self.module.log(msg=f"disable plugin version ({installed_plugin})")
                    installed_plugin.disable(force=True)

                    self.module.log(msg="remove plugin")
                    installed_plugin.remove(force=True)

                    self.__remove_plugin_information()

                result = dict(
                    changed = True,
                    failed = False,
                    msg = f"plugin {installed_plugin} was successfully removed."
                )

            except docker.errors.APIError as e:
                error = str(e)
                self.module.log(msg=f"{error}")

                result = dict(
                    changed = False,
                    failed = True,
                    msg = error
                )

            except Exception as e:
                error = str(e)
                self.module.log(msg=f"{error}")

                result = dict(
                    changed = False,
                    failed = True,
                    msg = error
                )
        else:
            result = dict(
                changed = False,
                failed = False,
                msg = "plugin is not installed."
            )

        return result

    def docker_config_value(self, value, default):
        """
        """
        config_data = self.__read_docker_config()

        config_value = config_data.get(value, None)
        if config_value:
            return config_value
        else:
            return default

    def __read_docker_config(self, config_file="/etc/docker/daemon.json"):
        """
        """
        self.module.log(msg=f"__read_docker_config(self, {config_file})")
        data = dict()

        if os.path.exists(config_file):
            self.module.log("  read")
            with open(config_file) as json_file:
                self.module.log("  {json_file}")
                data = json.load(json_file)
        else:
            self.module.log(f"  {config_file} doesnt exists.")
        self.module.log(msg=f"  {data}")

        return data

    def __write_plugin_information(self, data):
        """
        """
        self.module.log(msg=f"persist plugin information in '{self.plugin_information_file}'")

        with open(self.plugin_information_file, 'w') as fp:
            json_data = json.dumps(data, indent=2, sort_keys=False)
            fp.write(f'{json_data}\n')

    def __remove_plugin_information(self):
        """
        """
        if os.path.exists(self.plugin_information_file):
            os.remove(self.plugin_information_file)


# ---------------------------------------------------------------------------------------
# Module execution.
#


def main():

    args = dict(
        state = dict(
            default="present",
            choices=[
                "absent",
                "present",
                "test"
            ]
        ),
        #
        plugin_source = dict(
            required = True,
            type='str'
        ),
        plugin_version = dict(
            required = False,
            type="str",
            default = "latest"
        ),
        plugin_alias = dict(
            required = True,
            type='str'
        ),
        data_root=dict(
            type='str',
            default="/var/lib/docker"
        )
    )

    module = AnsibleModule(
        argument_spec = args,
        supports_check_mode = True,
    )

    dp = DockerPlugins(module)
    result = dp.run()

    module.log(msg=f"= result: {result}")

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
