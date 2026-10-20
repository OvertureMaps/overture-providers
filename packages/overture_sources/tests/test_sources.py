import pytest
from overture_sources import load_sources, theme_names


def test_themes_present():
    assert {
        "addresses",
        "base",
        "buildings",
        "divisions",
        "places",
        "transportation",
    } <= set(theme_names())


@pytest.mark.parametrize("theme", theme_names())
def test_sources_load(theme):
    assert load_sources(theme)


@pytest.mark.parametrize("name", ["nope", "../pyproject", "a\\b"])
def test_unknown_theme(name):
    with pytest.raises(KeyError):
        load_sources(name)
