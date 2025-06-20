# python 3 headers, required if submitting to Ansible

from __future__ import (absolute_import, print_function)
__metaclass__ = type

import operator as op
from packaging.version import Version
from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """
        Ansible file jinja2 tests
    """

    def filters(self):
        return {
            'registry_migrate': self.registry_migrate,
        }

    def registry_migrate(self, data, config_type, version):
        """
            # https://github.com/distribution/distribution/commit/fcb2deac0b6d2e9c5f840dcebe580b46d4e99a0f
        """
        # display.v(f"registry_migrate({data}, {config_type}, {version})")
        result = data.copy()

        if version:
            if self.version_compare(version, ">=", "3.0"):
                """
                """
                redis_addr = data.get("addr", None)
                redis_addrs = data.get("addrs", None)
                # redis_pool = data.get("pool", None)
                # redis_pool_maxidle = redis_pool.get("pool", None)
                # redis_pool_maxactive = redis_pool.get("pool", None)
                # redis_pool_idletimeout = redis_pool.get("pool", None)
                # display.v(f"redis_addr : {redis_addr}")
                # display.v(f"redis_addrs : {redis_addrs}")
                if redis_addr:
                    result.pop("addr")

                if redis_addr and not redis_addrs:
                    """ migrate """
                    result["addrs"] = [redis_addr]

                # if redis_pool:
                #     result.pop("pool")

        # display.v(f"return : {result}")
        return result

    def version_compare(self, ver1, specifier, ver2):
        """
        """
        lookup = {'<': op.lt, '<=': op.le, '==': op.eq, '>=': op.ge, '>': op.gt}

        try:
            return lookup[specifier](Version(ver1), Version(ver2))
        except KeyError:
            # unknown specifier
            return False
