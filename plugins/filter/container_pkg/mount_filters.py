from typing import Any, Dict, List

from ansible.utils.display import Display

from .base import ContainerBase

display = Display()


class MountFilters(ContainerBase):
    """Filters related to container volume and mount handling."""

    def filters(self) -> Dict[str, Any]:
        """
        Register available Jinja2 filters.

        Returns:
            dict: Mapping of filter names to callable methods.
        """
        display.vv("MountFilters::filters()")

        return {
            "container_volumes": self.container_volumes,
            "container_mounts": self.container_mounts,
            "validate_mountpoints": self.validate_mountpoints,
        }

    def container_volumes(self, data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extract and normalize volume definitions from container data.

        Returns:
            list: A list of dictionaries containing volume mappings and metadata.
        """
        display.vv("MountFilters::container_volumes(data)")

        result: List[Dict[str, str]] = []

        for container in data:
            volumes = container.get("volumes", [])
            if not isinstance(volumes, list):
                continue

            for volume_entry in volumes:
                if not isinstance(volume_entry, str):
                    continue

                values = volume_entry.split(":")
                if len(values) >= 2:
                    result.append({"local": values[0], "remote": values[1]})

        return result

    def container_mounts(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Return valid mount definitions from container data.

        Returns:
            list: A list of mount dictionaries with 'source_handling.create' = True.
        """
        display.vv("MountFilters::container_mounts(data)")

        result: List[Dict[str, Any]] = []

        # Defensive: ensure _get_keys_from_dict exists
        if not hasattr(self, "_get_keys_from_dict"):
            raise AttributeError(
                "Missing method _get_keys_from_dict required by container_mounts"
            )

        mounts = self._get_keys_from_dict(data, "mounts")
        merged = self._flatten_list(mounts)
        # merged = list(itertools.chain.from_iterable(mounts))

        for item in merged:
            if not isinstance(item, dict):
                continue

            source_handling = item.get("source_handling", {})
            if isinstance(source_handling, dict) and source_handling.get(
                "create", False
            ):
                result.append(item)

        return result

    def validate_mountpoints(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate mountpoint definitions and detect missing attributes.

        Args:
            data (list): List of container dictionaries.

        Returns:
            list: A list of invalid mount definitions with corresponding error messages.
        """
        display.vv("MountFilters::validate_mountpoints(data)")

        errors: List[Dict[str, Any]] = []
        valid_types = {"bind", "tmpfs", "volume"}

        for container in data:
            container_name = container.get("name")
            mounts = container.get("mounts", [])
            if not isinstance(mounts, list):
                continue

            for mount in mounts:
                if not isinstance(mount, dict):
                    continue

                missing = [k for k in ("source", "target", "type") if not mount.get(k)]
                invalid_type = mount.get("type") not in valid_types

                if missing or invalid_type:
                    errors.append(
                        {
                            "container": container_name,
                            "mount_definition": mount,
                            "error": ", ".join(missing or ["wrong type"]),
                        }
                    )

        return errors
