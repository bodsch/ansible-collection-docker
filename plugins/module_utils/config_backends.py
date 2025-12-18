#!/usr/bin/python3
# -*- coding: utf-8 -*-
# (c) 2023-2025, Bodo Schulz <bodo@boone-schulz.de>
# SPDX-License-Identifier: Apache-2.0

"""
config_backends.py
=====================

Dieses Modul bietet mehrere Serialisierungsstrategien (Writer),
um Python-Datenstrukturen in verschiedene Konfigurationsdateiformate
zu konvertieren.

Unterstützte Formate:
  - JSON
  - YAML
  - TOML
  - INI

Jeder Writer implementiert das `Writer`-Protokoll, das eine einheitliche API
bereitstellt, um Daten zu serialisieren (`dump`) und die zugehörige Dateiendung
(`ext`) bereitzustellen.

Beispiel:
---------
    from config_file_writer import JSONWriter, YAMLWriter

    data = {"app": {"port": 8080, "debug": True}}

    writer = YAMLWriter()
    yaml_text = writer.dump(data)
    print(yaml_text)

    json_writer = JSONWriter()
    with open(f"config.{json_writer.ext()}", "w") as f:
        f.write(json_writer.dump(data))
"""

from __future__ import annotations

import configparser
import io
import json
from typing import Any, Mapping, Protocol

# =============================================================================
# Protocol Definition
# =============================================================================


class Writer(Protocol):
    """
    Definiert die Schnittstelle, die alle Writer-Klassen implementieren müssen.

    Methoden:
        dump(data): Serialisiert die gegebenen Daten in einen String.
        ext(): Gibt die standardmäßige Dateiendung des Formats zurück.
    """

    def dump(self, data: Mapping[str, Any]) -> str:
        """Serialisiert Daten in den Zielformatstring."""
        ...

    def ext(self) -> str:
        """Dateiendung des Zielformats."""
        ...


# =============================================================================
# JSON Writer
# =============================================================================


class JSONWriter:
    """
    Serialisiert Python-Datenstrukturen in JSON.

    Unterstützt Unicode, sortiert keine Keys und erzeugt
    menschenlesbare Einrückungen.
    """

    def dump(self, data: Mapping[str, Any]) -> str:
        """Serialisiert Daten in JSON."""
        if isinstance(data, str):
            return data

        return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)

    def ext(self) -> str:
        """Dateiendung für JSON-Dateien."""
        return "json"


# =============================================================================
# YAML Writer
#
# =============================================================================


class YAMLWriter:
    """
    Serialisiert Python-Datenstrukturen in YAML.

    Erfordert die Installation von `PyYAML`.
    """

    def __init__(self) -> None:
        """Initialisiert den YAML-Writer und importiert PyYAML."""
        try:
            import yaml  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                "PyYAML ist erforderlich für YAML-Ausgabe: pip install pyyaml"
            ) from e
        self._yaml = yaml

    def dump(self, data: Mapping[str, Any]) -> str:
        """Serialisiert Daten in YAML."""
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
        """Dateiendung für YAML-Dateien."""
        return "yaml"


# =============================================================================
# TOML Writer
# =============================================================================


class TOMLWriter:
    """
    Serialisiert Python-Datenstrukturen in TOML.

    Versucht zuerst, `tomli-w` zu verwenden (empfohlen).
    Fällt bei Nichtverfügbarkeit auf das `toml`-Modul zurück.
    """

    def __init__(self) -> None:
        """Initialisiert die TOML-Engine."""
        self._mode = None
        try:
            import tomli_w  # type: ignore

            self._mode = ("tomli_w", tomli_w)
        except ImportError:
            try:
                import toml  # type: ignore

                self._mode = ("toml", toml)
            except ImportError as e:
                raise RuntimeError(
                    "TOML-Ausgabe benötigt tomli-w oder toml: pip install tomli-w"
                ) from e

    def dump(self, data: Mapping[str, Any]) -> str:
        """Serialisiert Daten in TOML."""
        if isinstance(data, str):
            return data

        mode, lib = self._mode
        if mode == "tomli_w":
            buf = io.BytesIO()
            lib.dump(data, buf)  # type: ignore[attr-defined]
            return buf.getvalue().decode("utf-8")

        return lib.dumps(data)  # type: ignore[attr-defined]

    def ext(self) -> str:
        """Dateiendung für TOML-Dateien."""
        return "toml"


# =============================================================================
# INI Writer
# =============================================================================


class INIWriter:
    """
    Serialisiert Python-Datenstrukturen in INI.

    - Top-Level-Dictionaries werden zu Sektionen.
    - Schlüssel außerhalb von Dictionaries landen in der `[DEFAULT]`-Sektion.
    - Komplexe Werte (z. B. Listen oder verschachtelte Objekte) werden als JSON serialisiert.
    """

    def dump(self, data: Mapping[str, Any]) -> str:
        """Serialisiert Daten in das INI-Format."""
        if isinstance(data, str):
            return data

        cp = configparser.ConfigParser()
        default_values: dict[str, str] = {}

        for key, value in data.items():
            if isinstance(value, Mapping):
                cp.add_section(key)
                for subkey, subvalue in value.items():
                    cp[key][str(subkey)] = self._to_str(subvalue)
            else:
                default_values[str(key)] = self._to_str(value)

        if default_values:
            cp["DEFAULT"] = default_values

        with io.StringIO() as buffer:
            cp.write(buffer)
            return buffer.getvalue()

    def _to_str(self, value: Any) -> str:
        """
        Konvertiert beliebige Werte in Strings, wie sie in INI-Dateien erlaubt sind.
        """
        if isinstance(value, (str, int, float, bool)) or value is None:
            if value is True:
                return "true"
            if value is False:
                return "false"
            if value is None:
                return ""
            return str(value)

        # komplexe Datentypen (z. B. Listen, Dicts) als JSON serialisieren
        return json.dumps(value, ensure_ascii=False)

    def ext(self) -> str:
        """Dateiendung für INI-Dateien."""
        return "ini"
