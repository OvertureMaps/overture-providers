"""Overture source registry JSON files, one per theme."""

import json
from importlib.resources import files
from typing import Any

_PACKAGE = files(__package__)


def theme_names() -> list[str]:
    """Return the sorted theme names that have a packaged sources file."""
    return sorted(
        p.name.removesuffix(".json")
        for p in _PACKAGE.iterdir()
        if p.name.endswith(".json")
    )


def load_sources(theme: str) -> dict[str, Any]:
    """Return the parsed sources file for ``theme`` (the JSON file stem).

    Raises ``KeyError`` if no file exists for that theme.
    """
    path = _PACKAGE / f"{theme}.json"
    if "/" in theme or "\\" in theme or not path.is_file():
        raise KeyError(f"unknown theme: {theme!r}")
    return json.loads(path.read_text(encoding="utf-8"))
