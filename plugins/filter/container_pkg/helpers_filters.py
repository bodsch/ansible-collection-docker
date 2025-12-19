from typing import Any, Dict, List, Union

from ansible.utils.display import Display

display = Display()


class HelpersFilters:
    """A collection of helper Jinja2 filters for Ansible templates."""

    def filters(self) -> Dict[str, Any]:
        """
        Register available Jinja2 filters.

        Returns:
            dict: Mapping of filter names to callable methods.
        """
        display.vv("HelpersFilters::filters()")

        return {
            "files_available": self.files_available,
            "remove_custom_fields": self.remove_custom_fields,
            "remove_source_handling": self.remove_source_handling,
        }

    def files_available(self, data: List[Dict[str, Any]]) -> List[Any]:
        """
        Extract items from a list of dictionaries where 'stat.exists' is True.

        Args:
            data (list): List of dictionaries typically returned by Ansible's 'stat' module results.

        Returns:
            list: List of 'item' values where 'stat.exists' is True.
        """
        display.vv(f"HelpersFilters::files_available({data})")

        result: List[Any] = []

        for entry in data:
            if isinstance(entry, dict) and entry.get("stat", {}).get("exists", False):
                result.append(entry.get("item"))

        return result

    def remove_custom_fields(
        self, data: Union[List[str], str]
    ) -> Union[List[str], str]:
        """
        Remove custom field information from string entries.

        This filter cleans strings containing additional metadata separated by '|'.
        It returns only the base value before the separator.

        Args:
            data (list or str): List of strings or a single string potentially containing '|'.

        Returns:
            list or str: Cleaned string(s) without custom metadata.
        """
        display.vv(f"HelpersFilters::remove_custom_fields({data})")

        if isinstance(data, list):
            result: List[str] = [v.split("|")[0] for v in data if isinstance(v, str)]
        else:
            result = data

        return result

    def remove_source_handling(
        self, data: Union[List[Dict[str, Any]], Dict[str, Any]]
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Remove 'source_handling' key(s) from dictionaries or lists of dictionaries.

        Args:
            data (list or dict): Data structure potentially containing the 'source_handling' key.

        Returns:
            list or dict: Structure with the 'source_handling' key removed where present.
        """
        display.vv(f"HelpersFilters::remove_source_handling({data})")

        if isinstance(data, list):
            data = self._del_keys_from_dict(data, "source_handling")
        elif isinstance(data, dict):
            data.pop("source_handling", None)

        return data

    def _del_keys_from_dict(
        self, data: List[Dict[str, Any]], key: str
    ) -> List[Dict[str, Any]]:
        """
        Helper method to remove a specific key from all dictionaries in a list.

        Args:
            data (list): List of dictionaries.
            key (str): Key to remove from each dictionary.

        Returns:
            list: Modified list with the specified key removed from all entries.
        """
        for entry in data:
            if isinstance(entry, dict):
                entry.pop(key, None)
        return data
