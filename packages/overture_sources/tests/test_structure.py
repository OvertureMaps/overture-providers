"""Structural checks for the source registry. Sources are an append-only log of
free-form records, so only invariants that every consumer relies on are enforced."""

import re
from collections import Counter

import pytest
from overture_sources import load_sources, theme_names

REQUIRED = {
    "source_name",
    "dataset_name",
    "inception_date",
    "source",
    "license",
    "coverage",
    "refresh_schedule",
    "known_issues",
    "notes",
}
THEMES = [t for t in theme_names() if t != "property_descriptions"]


def test_themes_present():
    assert set(THEMES) == {
        "addresses",
        "base",
        "buildings",
        "divisions",
        "places",
        "transportation",
    }


@pytest.mark.parametrize("theme", THEMES)
def test_datasets_have_required_fields(theme):
    sources = load_sources(theme)
    assert isinstance(sources["license_priority"], dict)
    assert sources["datasets"]
    for dataset in sources["datasets"]:
        missing = REQUIRED - dataset.keys()
        assert not missing, (dataset.get("dataset_name"), missing)
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", dataset["inception_date"])
        assert isinstance(dataset["license"]["type"], str)


@pytest.mark.parametrize("theme", THEMES)
def test_dataset_keys_unique(theme):
    keys = Counter(
        (d["source_name"], d["dataset_name"]) for d in load_sources(theme)["datasets"]
    )
    assert not [k for k, n in keys.items() if n > 1]


def test_property_descriptions():
    assert load_sources("property_descriptions")["properties"]
