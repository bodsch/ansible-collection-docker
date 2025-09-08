# file: config_file_writer.py
from __future__ import annotations
# from dataclasses import dataclass
# from pathlib import Path
from typing import Any, Mapping, Protocol
import io
import json
import configparser


# ---- Writer-Strategien -------------------------------------------------------


class Writer(Protocol):
    def dump(self, data: Mapping[str, Any]) -> str:
        """Serialisiert Daten in den Zielformatstring."""
        ...

    def ext(self) -> str:
        """Dateiendung des Zielformats."""
        ...


class JSONWriter:
    def dump(self, data: Mapping[str, Any]) -> str:
        if isinstance(data, str):
            return data

        return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)

    def ext(self) -> str:
        return "json"


class YAMLWriter:
    def __init__(self) -> None:
        try:
            import yaml  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "PyYAML ist erforderlich für YAML-Ausgabe: pip install pyyaml"
            ) from e
        self._yaml = yaml

    def dump(self, data: Mapping[str, Any]) -> str:

        if isinstance(data, str):
            return data

        return self._yaml.safe_dump(
            data,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            indent=2,
        )

    def ext(self) -> str:
        return "yaml"


class TOMLWriter:
    def __init__(self) -> None:
        # bevorzugt 'tomli-w' (stabil, write-only), fällt zurück auf 'toml'
        self._mode = None
        try:
            import tomli_w  # type: ignore
            self._mode = ("tomli_w", tomli_w)
        except Exception:
            try:
                import toml  # type: ignore
                self._mode = ("toml", toml)
            except Exception as e:
                raise RuntimeError(
                    "TOML-Ausgabe benötigt tomli-w oder toml: pip install tomli-w"
                ) from e

    def dump(self, data: Mapping[str, Any]) -> str:

        if isinstance(data, str):
            return data

        mode, lib = self._mode
        if mode == "tomli_w":
            buf = io.BytesIO()
            lib.dump(data, buf)  # type: ignore[attr-defined]
            return buf.getvalue().decode("utf-8")
        else:
            return lib.dumps(data)  # type: ignore[attr-defined]

    def ext(self) -> str:
        return "toml"


class INIWriter:
    """
        Top-Level-Dicts werden zu Sektionen. Nicht-Dict-Werte landen in [DEFAULT].
    """

    def dump(self, data: Mapping[str, Any]) -> str:
        """
        """
        if isinstance(data, str):
            return data

        cp = configparser.ConfigParser()
        default_acc: dict[str, str] = {}
        for k, v in data.items():
            if isinstance(v, Mapping):
                section = cp[k]  # auto-create on set
                for sk, sv in v.items():
                    section[str(sk)] = self._to_str(sv)
            else:
                default_acc[str(k)] = self._to_str(v)
        if default_acc:
            cp["DEFAULT"] = default_acc
        with io.StringIO() as s:
            cp.write(s)
            return s.getvalue()

    def _to_str(self, v: Any) -> str:
        if isinstance(v, (str, int, float, bool)) or v is None:
            return "true" if v is True else "false" if v is False else "" if v is None else str(v)

        return json.dumps(v, ensure_ascii=False)  # komplexe Werte als JSON

    def ext(self) -> str:
        return "ini"
