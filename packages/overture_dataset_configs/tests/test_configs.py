from pathlib import Path

import pytest
from overture_dataset_configs import (
    load_config,
    load_license_policy,
    provider_names,
)
from overture_dataset_configs.dataset import Dataset
from overture_dataset_configs.schema import THEMES, validate_all, validate_file

DATASETS = Path(__file__).parent.parent / "overture_dataset_configs" / "datasets"
FILES = sorted(DATASETS.glob("*.json"))

# Resources that intentionally feed no theme.
UNTAGGED = {"osm_planet_history"}


def test_configs_present():
    assert FILES


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.stem)
def test_config_is_valid(path):
    validate_file(path)


def test_provider_labels_unique():
    assert validate_all(FILES) == []


def test_provider_names_match_files():
    assert provider_names() == [p.stem for p in FILES]


def test_load_config_by_provider_name():
    for name in provider_names():
        assert load_config(name)["provider"]["label"] == name


@pytest.mark.parametrize("name", ["nope", "../pyproject", "a\\b"])
def test_load_config_unknown(name):
    with pytest.raises(KeyError):
        load_config(name)


def test_themes_match_license_policy():
    assert set(THEMES) == set(load_license_policy())


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.stem)
def test_theme_values_are_known(path):
    config = load_config(path.stem)
    declared = [config.get("themes") or []]
    declared += [r.get("themes") or [] for r in config["resources"]]
    for themes in declared:
        assert set(themes) <= set(THEMES), themes
        assert len(themes) == len(set(themes)), themes


def test_every_resource_resolves_to_a_theme():
    untagged = {
        ds.dataset_id
        for path in FILES
        for ds in Dataset.all_from_file(path)
        if not ds.themes
    }
    assert untagged == UNTAGGED


# The delivery.method values consistent with each data_download.type.
METHODS_BY_DOWNLOAD_TYPE = {
    "s3": {"bucket"},
    "http": {"api", "file_download"},
    "hf": {"file_download"},
}


def test_delivery_method_matches_data_download():
    mismatched = []
    for path in FILES:
        for ds in Dataset.all_from_file(path):
            method = ds.delivery.get("method")
            download = ds.collection.get("data_download")
            if method and download:
                if method not in METHODS_BY_DOWNLOAD_TYPE[download["type"]]:
                    mismatched.append((ds.dataset_id, download["type"], method))
    assert mismatched == []
