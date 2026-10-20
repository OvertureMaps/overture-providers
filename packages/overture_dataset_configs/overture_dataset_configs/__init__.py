"""Public Overture dataset license/policy configs, addressable by provider name."""

import json
from importlib.resources import files
from importlib.resources.abc import Traversable
from typing import Any

_DATASETS = files(__package__) / "datasets"


def _path(provider: str) -> Traversable:
    return _DATASETS / f"{provider}.json"


def provider_names() -> list[str]:
    """Return the sorted provider labels that have a packaged config."""
    return sorted(
        p.name.removesuffix(".json")
        for p in _DATASETS.iterdir()
        if p.name.endswith(".json")
    )


def load_config(provider: str) -> dict[str, Any]:
    """Return the parsed config for ``provider`` (the JSON file stem).

    Raises ``KeyError`` if no config exists for that provider.
    """
    path = _path(provider)
    if "/" in provider or "\\" in provider or not path.is_file():
        raise KeyError(f"unknown provider: {provider!r}")
    return json.loads(path.read_text(encoding="utf-8"))
