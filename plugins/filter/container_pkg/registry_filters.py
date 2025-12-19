import operator as op
from typing import Any, Dict, List, Optional, Union

from ansible.errors import AnsibleFilterError
from ansible.utils.display import Display
from packaging.version import Version

from .base import ContainerBase

display = Display()


class RegistryFilters(ContainerBase):
    """Filters for working with registry configuration data."""

    def filters(self) -> Dict[str, Any]:
        """
        Register available Jinja2 filters.

        Returns:
            dict: Mapping of filter names to callable methods.
        """
        display.vv("RegistryFilters::filters()")

        return {
            "registry_migrate": self.registry_migrate,
            "combine_registries": self.combine_registries,
        }

    def registry_migrate(
        self,
        data: Dict[str, Any],
        config_type: Optional[str],
        version: Optional[str],
    ) -> Dict[str, Any]:
        """
        Migrate old registry configurations to a new schema based on the version.

        This filter inspects registry configuration data and updates
        deprecated keys such as `addr` to the new `addrs` list format.

        Reference:
            https://github.com/distribution/distribution/commit/fcb2deac0b6d2e9c5f840dcebe580b46d4e99a0f

        Args:
            data (dict): The registry configuration to migrate.
            config_type (str, optional): The registry configuration type.
            version (str, optional): The target registry version.

        Returns:
            dict: Updated registry configuration dictionary.
        """
        display.vv(
            f"RegistryFilters::registry_migrate({data}, {config_type}, {version})"
        )

        result: Dict[str, Any] = data.copy()

        if version and self.version_compare(version, ">=", "3.0"):
            redis_addr: Optional[str] = data.get("addr")
            redis_addrs: Optional[List[str]] = data.get("addrs")

            if redis_addr:
                result.pop("addr", None)

            # Migrate single addr to list-based addrs if missing
            if redis_addr and not redis_addrs:
                result["addrs"] = [redis_addr]

        return result

    def combine_registries(
        self,
        data: Union[List[Dict[str, Any]], Dict[str, Any]],
        defaults: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Merge user-provided registry configurations with default values.

        This filter combines either a single registry definition or a list
        of registries with a provided list of default settings.

        Args:
            data (list or dict): User-defined registry configuration(s).
            defaults (list): A list containing one or more default registry dictionaries.

        Returns:
            list: A list of merged and cleaned registry configurations.
        """
        display.vv(f"RegistryFilters::combine_registries({data}, {defaults})")

        result: List[Dict[str, Any]] = []

        result = [self._safe_merge(defaults[0], entry) for entry in data]

        if not defaults:
            raise AnsibleFilterError(
                "combine_registries requires at least one default configuration"
            )

        _default: Dict[str, Any] = defaults[0].copy()
        _data = data.copy() if isinstance(data, (dict, list)) else {}

        if isinstance(_data, dict):
            # Old-style single registry definition
            _merged = {**_default, **_data}
            cleaned = {k: v for k, v in _merged.items() if v}
            result.append(cleaned)

        elif isinstance(_data, list):
            for entry in _data:
                if not isinstance(entry, dict):
                    continue

                _merged = {**_default, **entry}
                cleaned = {k: v for k, v in _merged.items() if v}
                result.append(cleaned)

        return result

    def version_compare(self, ver1: str, specifier: str, ver2: str) -> bool:
        """
        Compare two semantic version strings.

        Args:
            ver1 (str): The first version to compare.
            specifier (str): The comparison operator ('<', '<=', '==', '>=', '>').
            ver2 (str): The second version to compare.

        Returns:
            bool: True if the comparison holds, False otherwise.
        """
        display.vv(
            f"RegistryFilters::version_compare(ver1={ver1}, specifier={specifier}, ver2={ver2})"
        )

        lookup = {
            "<": op.lt,
            "<=": op.le,
            "==": op.eq,
            ">=": op.ge,
            ">": op.gt,
        }

        try:
            return lookup[specifier](Version(ver1), Version(ver2))
        except KeyError as e:
            display.v(f"Invalid specifier '{specifier}': {e}")
            return False
        except Exception as e:
            display.v(f"Error comparing versions '{ver1}' and '{ver2}': {e}")
            return False
