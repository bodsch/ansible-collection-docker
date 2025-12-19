import itertools
from typing import Any, Dict, List, Optional, Set

from ansible.errors import AnsibleFilterError
from ansible.utils.display import Display

display = Display()


class ContainerFilters:
    """Filters for general container data manipulation."""

    def filters(self) -> Dict[str, Any]:
        """
        Register available Jinja2 filters.

        Returns:
            dict: Mapping of filter names to their corresponding callable functions.
        """
        display.vv("ContainerFilters::filters()")

        return {
            "container_names": self.container_names,
            "container_images": self.container_images,
            "container_state": self.container_state,
            "container_filter": self.container_filter,
            "container_filter_by": self.container_filter_by,
            "container_environnments": self.container_environnments,
            "container_volumes": self.container_volumes,
            "container_mounts": self.container_mounts,
        }

    def container_names(self, data: List[Dict[str, Any]]) -> List[str]:
        """Return a list of container names."""
        display.vv(f"ContainerFilters::container_names({data})")

        if not isinstance(data, list):
            raise AnsibleFilterError("Expected a list of containers.")

        return [c.get("name") for c in data if "name" in c]

    def container_images(self, data: List[Dict[str, Any]]) -> List[str]:
        """Return all container image names."""
        display.vv(f"ContainerFilters::container_images({data})")

        return [c.get("image") for c in data if "image" in c]

    def container_state(
        self,
        data: List[Dict[str, Any]],
        state: str = "present",
        return_value: str = "image",
    ) -> List[str]:
        """Filter containers by state and return a specific attribute."""
        display.vv(
            f"ContainerFilters::container_state({data}, {state}, {return_value})"
        )

        valid_states: Set[str] = {"started", "stopped", "present", "absent"}
        if state not in valid_states:
            raise AnsibleFilterError(f"Invalid state '{state}'.")

        present_states: Set[str] = {"started", "present"}
        state_filter: Set[str] = (
            present_states if state in present_states else {"stopped", "absent"}
        )

        return sorted(
            {
                c.get(return_value)
                for c in data
                if isinstance(c, dict)
                and c.get("state") in state_filter
                and c.get(return_value)
            }
        )

    def container_filter(
        self, data: List[Dict[str, Any]], state: List[str]
    ) -> Dict[str, Any]:
        """
        Aggregate container information for specific states.

        Args:
            data (list): List of container dictionaries.
            state (list): States to include or ignore (e.g., ["started", "stopped"]).

        Returns:
            dict: A summary of container attributes such as names, images, mounts, and environments.
        """
        display.vv(f"ContainerFilters::container_filter(data: {data}, state: {state})")

        result: Dict[str, Any] = {}
        _data = data.copy()

        container_launch: List[Any] = []
        if len(state) > 0:
            container_launch = self.container_ignore_state(_data, state)

        container_names: List[str] = self.container_names(_data)
        container_images: List[str] = self.container_state(_data)
        container_mounts: List[Dict[str, Any]] = self.container_mounts(_data)
        container_volumes: List[Dict[str, str]] = self.container_volumes(_data)
        container_env: List[Dict[str, Any]] = self.container_environnments(_data)

        result = dict(
            names=container_names,
            images=container_images,
            launch=container_launch,
            mounts=container_mounts,
            volumes=container_volumes,
            environnments=container_env,
        )
        return result

    def container_filter_by(
        self,
        data: List[Dict[str, Any]],
        filter_by: str,
        filter_values: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Filter containers by a given key and a list of allowed values.

        Args:
            data (list): List of container dictionaries.
            filter_by (str): The key to filter by (e.g., "name", "hostname", or "image").
            filter_values (list): Values to match against.

        Returns:
            list: Filtered container dictionaries.
        """
        display.vv(
            f"ContainerFilters::container_filter_by(data, {filter_by}, {filter_values})"
        )

        if filter_by not in {"name", "hostname", "image"}:
            return data

        d = data.copy()

        for entry in d:
            if filter_by == "name":
                name = entry.get("name")
                if name not in filter_values:
                    data.remove(entry)
            elif filter_by == "hostname":
                hostname = entry.get("hostname")
                if hostname not in filter_values:
                    data.remove(entry)
            elif filter_by == "image":
                image = entry.get("image")
                if image not in filter_values:
                    data.remove(entry)

        return data

    def container_environnments(
        self,
        data: List[Dict[str, Any]],
        want_list: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extract only selected environment-related keys from container definitions.

        Args:
            data (list): List of container dictionaries.
            want_list (list, optional): Keys to include in the result.

        Returns:
            list: A filtered list of dictionaries containing only requested keys.
        """
        display.vv(
            f"ContainerFilters::container_environnments(self, data, {want_list})"
        )

        if want_list is None:
            want_list = [
                "name",
                "hostname",
                "environments",
                "properties",
                "property_files",
                "config_files",
            ]

        result: List[Dict[str, Any]] = []
        _data = data.copy()

        for i in _data:
            res = {k: v for k, v in i.items() if k in want_list}
            result.append(res)

        return result

    def container_volumes(self, data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extract and normalize volume definitions from container data.

        Returns:
            list: A list of dictionaries containing volume mappings and metadata.
        """
        display.vv("ContainerFilters::container_volumes(data)")

        result: List[Dict[str, str]] = []

        for container in data:
            for v in container.get("volumes", []):
                values = v.split(":")
                if len(values) >= 2:
                    result.append({"local": values[0], "remote": values[1]})

        return result

    def container_mounts(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Return valid mount definitions from container data.

        Returns:
            list: A list of mount dictionaries with 'source_handling.create' = True.
        """
        display.vv("ContainerFilters::container_mounts(data)")

        result: List[Dict[str, Any]] = []

        mounts = self._get_keys_from_dict(data, "mounts")
        merged = list(itertools.chain(*mounts))

        for item in merged:
            if item.get("source_handling", {}).get("create"):
                result.append(item)

        return result
