from pathlib import Path

import pytest
from overture_dataset_configs import load_config, provider_names
from overture_dataset_configs.schema import validate_all, validate_file

DATASETS = Path(__file__).parent.parent / "overture_dataset_configs" / "datasets"
FILES = sorted(DATASETS.glob("*.json"))


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


def test_natural_earth_disputed_areas():
    from overture_dataset_configs.dataset import Dataset
    from overture_dataset_configs.license_policy import load_policy

    ds = Dataset.from_name("natural_earth", "admin_0_disputed_areas_10m")
    assert ds.dataset_id == "natural_earth_admin_0_disputed_areas_10m"
    assert ds.license_type == "LicenseRef-Public-Domain-Natural-Earth"
    assert ds.download_url == (
        "https://naturalearth.s3.amazonaws.com/10m_cultural/"
        "ne_10m_admin_0_disputed_areas.zip"
    )
    assert load_policy().is_allowed("divisions", ds.license_type)
