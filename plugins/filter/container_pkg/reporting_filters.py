from typing import Any, Dict, List, Union

from ansible.errors import AnsibleFilterError
from ansible.utils.display import Display

display = Display()


class ReportingFilters:
    """Filters for analyzing and reporting container operation results."""

    def filters(self) -> Dict[str, Any]:
        """
        Register available Jinja2 filters.

        Returns:
            dict: Mapping of filter names to callable methods.
        """
        display.vv("ReportingFilters::filters()")

        return {
            "reporting": self.reporting,
            "container_ignore_state": self.container_ignore_state,
            "changed": self.filter_changed,
            "update": self.filter_update,
            "properties_changed": self.filter_properties_changed,
        }

    def filter_changed(
        self, data: Union[List[Dict[str, Any]], Dict[str, Any]]
    ) -> List[Any]:
        """Return a list of items where 'changed' is True."""
        display.vv("ReportingFilters::filter_changed(data)")

        result: List[Any] = []

        if isinstance(data, dict):
            data = data.get("results", [])

        for entry in data:
            if isinstance(entry, dict) and entry.get("changed", False):
                item = entry.get("item")
                if item is not None:
                    result.append(item)

        return result

    def filter_properties_changed(
        self, data: Union[List[Dict[str, Any]], Dict[str, Any]]
    ) -> List[str]:
        """Return a list of container property names that changed."""
        display.vv("ReportingFilters::filter_properties_changed(data)")

        result: List[str] = []

        if isinstance(data, dict):
            data = data.get("results", [])

        for entry in data:
            if not isinstance(entry, dict):
                continue

            if entry.get("changed", False):
                item_name = entry.get("item", {}).get("name")
                if item_name:
                    result.append(item_name)

        return result

    def filter_update(
        self, data: List[Dict[str, Any]], update: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Add 'recreate=true' to changed container entries.

        Args:
            data (list): List of container definitions.
            update (list): List of container names or image identifiers to flag for recreation.

        Returns:
            list: Updated list of container dictionaries.
        """
        display.vv("ReportingFilters::filter_update(data, update)")

        for change in update:
            for container in data:
                if container.get("image") == change or container.get("name") == change:
                    container["recreate"] = "true"

        return data

    def reporting(
        self, data: Union[Dict[str, Any], List[Dict[str, Any]]], report_for: str
    ) -> List[Any]:
        """Create a filtered report of changed or failed containers."""
        display.vv("ReportingFilters::reporting(data, report_for)")

        states: List[Dict[str, Any]] = []
        result: List[Any] = []

        if isinstance(data, dict):
            results = data.get("results", [])
        elif isinstance(data, list):
            results = data
        else:
            raise AnsibleFilterError(
                "Invalid data structure provided to reporting() filter."
            )

        for entry in results:
            if not isinstance(entry, dict):
                continue

            failed = entry.get("failed", False)
            changed = entry.get("changed", False)

            if report_for == "failed" and failed:
                states.append(entry)
            elif report_for == "changed" and changed:
                states.append(entry)

        for item in states:
            container_data = item.get("item", {})
            name = container_data.get("name")
            hostname = container_data.get("hostname")
            image = container_data.get("image")
            msg = item.get("msg")

            if report_for == "changed":
                if hostname:
                    result.append(hostname)
                elif name:
                    result.append(name)
                elif image:
                    result.append(image)

            elif report_for == "failed":
                error_entry: Dict[str, Any] = {}
                if hostname:
                    error_entry[hostname] = msg
                elif name:
                    error_entry[name] = msg
                elif image:
                    error_entry[image] = msg

                if error_entry:
                    result.append(error_entry)

        return result

    def container_ignore_state(
        self, data: List[Dict[str, Any]], ignore_states: Union[List[str], None] = None
    ) -> List[Dict[str, Any]]:
        """Filter out containers with specific states."""
        display.vv(f"ReportingFilters::container_ignore_state(data, {ignore_states})")

        if ignore_states is None:
            ignore_states = ["present"]

        _data = data.copy()

        ignored = [i for i in _data if i.get("state", "started") in ignore_states]
        result = [i for i in _data if i.get("state", "started") not in ignore_states]

        ignore_container = [i.get("name") for i in ignored if i.get("name")]
        launch_container = [i.get("name") for i in result if i.get("name")]

        display.vv(f" = ignore container: {ignore_container}")
        display.vv(f" = launch container: {launch_container}")

        return result
