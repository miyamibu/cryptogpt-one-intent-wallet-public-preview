#!/usr/bin/env python3
"""Strict JSON/YAML helpers used by release validators.

JSON parsing is delegated to canonical_hashes.strict_load_json so duplicate keys,
floats, NaN and Infinity are rejected. YAML parsing rejects duplicate keys and
recursive aliases. These helpers are intentionally small enough to audit.
"""
from __future__ import annotations

import datetime as dt
import math
from pathlib import Path
from typing import Any

import yaml

from canonical_hashes import strict_load_json


class StrictDataError(ValueError):
    pass


class StrictSafeLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: StrictSafeLoader, node: yaml.nodes.MappingNode, deep: bool = False) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as exc:
            raise StrictDataError(f"unhashable YAML mapping key at line {key_node.start_mark.line + 1}") from exc
        if duplicate:
            raise StrictDataError(
                f"duplicate YAML key {key!r} at line {key_node.start_mark.line + 1}, column {key_node.start_mark.column + 1}"
            )
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


def _compose_node(self: StrictSafeLoader, parent: yaml.nodes.Node | None, index: int | None) -> yaml.nodes.Node:
    if self.check_event(yaml.AliasEvent):
        event = self.peek_event()
        raise StrictDataError(
            f"YAML aliases are prohibited in release data at line {event.start_mark.line + 1}, column {event.start_mark.column + 1}"
        )
    return yaml.SafeLoader.compose_node(self, parent, index)


StrictSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)
StrictSafeLoader.compose_node = _compose_node  # type: ignore[method-assign]


def _validate_yaml_value(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise StrictDataError(f"non-finite YAML float at {path}")
        return
    if isinstance(value, (dt.date, dt.datetime)):
        raise StrictDataError(f"implicit YAML timestamp is prohibited at {path}; quote it as a string")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_yaml_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, (str, bool, int)):
                raise StrictDataError(f"unsupported YAML mapping key type at {path}: {type(key).__name__}")
            _validate_yaml_value(item, f"{path}.{key}")
        return
    raise StrictDataError(f"unsupported YAML value type at {path}: {type(value).__name__}")


def strict_load_yaml(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        value = yaml.load(text, Loader=StrictSafeLoader)
    except (yaml.YAMLError, StrictDataError) as exc:
        raise StrictDataError(str(exc)) from exc
    if value is None:
        raise StrictDataError("empty YAML document")
    _validate_yaml_value(value)
    return value


def strict_load(path: Path) -> Any:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return strict_load_json(path)
    if suffix in {".yaml", ".yml"}:
        return strict_load_yaml(path)
    raise StrictDataError(f"unsupported strict-data extension: {path}")
