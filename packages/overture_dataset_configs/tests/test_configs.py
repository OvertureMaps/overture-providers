import json
from pathlib import Path

import pytest
from overture_dataset_configs import load_config, provider_names
from overture_dataset_configs.schema import main, validate_all, validate_file

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


def _write(tmp_path, name, data):
    path = tmp_path / name
    path.write_text(json.dumps(data) if not isinstance(data, str) else data)
    return path


def test_validate_rejects_bad_files(tmp_path):
    good = load_config("linz")
    unknown_key = {**good, "extra": 1}
    wrong_label = {**good, "provider": {**good["provider"], "label": "other"}}
    dupes = {**good, "resources": good["resources"] * 2}
    with pytest.raises(ValueError, match="snake_case"):
        validate_file(_write(tmp_path, "Bad-Name.json", good))
    with pytest.raises(ValueError):
        validate_file(_write(tmp_path, "linz.json", unknown_key))
    with pytest.raises(ValueError, match="must match file stem"):
        validate_file(_write(tmp_path, "linz.json", wrong_label))
    with pytest.raises(ValueError, match="duplicate resource labels"):
        validate_file(_write(tmp_path, "linz.json", dupes))
    with pytest.raises(ValueError, match="could not read"):
        validate_file(tmp_path / "missing.json")


def test_validate_all_flags_duplicate_providers(tmp_path):
    good = load_config("linz")
    a = _write(tmp_path, "linz.json", good)
    other = tmp_path / "sub"
    other.mkdir()
    b = _write(other, "linz.json", good)
    errors = validate_all([a, b])
    assert len(errors) == 1 and "already used" in str(errors[0][1])


def test_license_attribution_required(tmp_path):
    good = load_config("linz")
    resource = good["resources"][0]
    resource["collection"]["license"]["attribution"] = ""
    with pytest.raises(ValueError, match="attribution must be non-empty"):
        validate_file(_write(tmp_path, "linz.json", good))


def test_data_download_scheme_mismatch(tmp_path):
    good = load_config("linz")
    good["resources"][0]["collection"]["data_download"]["type"] = "s3"
    with pytest.raises(ValueError, match="url scheme does not match"):
        validate_file(_write(tmp_path, "linz.json", good))


def test_main(tmp_path, capsys):
    assert main([]) == 2
    assert main([str(FILES[0])]) == 0
    bad = _write(tmp_path, "linz.json", "{}")
    assert main([str(bad)]) == 1
    assert "FAIL" in capsys.readouterr().err
