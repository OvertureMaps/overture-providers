"""Tests for the Dataset class.

See ``test_schema.py`` for the strict pydantic validator's tests.
"""

import json

import pytest

from overture_dataset_configs.dataset import DATASETS_DIR, Dataset

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def single_resource_file(tmp_path):
    """Write a minimal single-resource dataset JSON file and return its path."""
    data = {
        "provider": {
            "label": "acme",
            "name": "Acme Corp",
            "url": {"primary": "https://acme.example.com"},
        },
        "resources": [
            {
                "label": "widgets",
                "name": "Acme Widgets",
                "collection": {
                    "license": {"type": "MIT"},
                    "coverage": {"global": True},
                    "data_location": {"primary": "s3://acme/widgets"},
                },
                "ingestion": {"format": "parquet"},
                "matching": {"strategy": "exact"},
            }
        ],
    }
    p = tmp_path / "acme.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


@pytest.fixture()
def multi_resource_file(tmp_path):
    """Write a two-resource dataset JSON file and return its path."""
    data = {
        "provider": {
            "label": "globex",
            "name": "Globex Inc",
            "url": {"primary": "https://globex.example.com"},
        },
        "resources": [
            {
                "label": "buildings",
                "name": "Globex Buildings",
                "collection": {},
                "ingestion": {},
                "matching": {},
            },
            {
                "label": "roads",
                "name": "Globex Roads",
                "collection": {"license": {"type": "ODbL"}},
                "ingestion": {"format": "geojson"},
                "matching": {},
            },
        ],
    }
    p = tmp_path / "globex.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


@pytest.fixture()
def empty_resources_file(tmp_path):
    """Write a dataset JSON file with no resources."""
    data = {
        "provider": {"label": "empty", "name": "Empty", "url": {}},
        "resources": [],
    }
    p = tmp_path / "empty.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ── from_file: single resource ──────────────────────────────────────────────


class TestFromFileSingleResource:
    def test_loads_by_name(self, single_resource_file):
        ds = Dataset.from_file(single_resource_file, resource="widgets")
        assert ds.dataset_id == "acme_widgets"
        assert ds.provider_label == "acme"
        assert ds.provider_name == "Acme Corp"
        assert ds.resource_label == "widgets"
        assert ds.resource_name == "Acme Widgets"

    def test_auto_selects_when_only_one(self, single_resource_file):
        ds = Dataset.from_file(single_resource_file)
        assert ds.resource_label == "widgets"

    def test_pipeline_sections(self, single_resource_file):
        ds = Dataset.from_file(single_resource_file, resource="widgets")
        assert ds.collection["license"]["type"] == "MIT"
        assert ds.ingestion["format"] == "parquet"
        assert ds.matching["strategy"] == "exact"

    def test_convenience_properties(self, single_resource_file):
        ds = Dataset.from_file(single_resource_file, resource="widgets")
        assert ds.license_type == "MIT"
        assert ds.coverage == {"global": True}
        assert ds.data_location == {"primary": "s3://acme/widgets"}

    def test_repr_and_str(self, single_resource_file):
        ds = Dataset.from_file(single_resource_file, resource="widgets")
        assert "acme_widgets" in repr(ds)
        assert str(ds) == "acme_widgets"

    def test_provider_url(self, single_resource_file):
        ds = Dataset.from_file(single_resource_file, resource="widgets")
        assert ds.provider_url == {"primary": "https://acme.example.com"}

    def test_provider_data_and_resource_data(self, single_resource_file):
        ds = Dataset.from_file(single_resource_file, resource="widgets")
        assert ds.provider_data["label"] == "acme"
        assert ds.resource_data["label"] == "widgets"

    def test_refresh_schedule_defaults_to_empty_dict(self, single_resource_file):
        ds = Dataset.from_file(single_resource_file, resource="widgets")
        assert ds.refresh_schedule == {}


# ── from_file: multi resource ───────────────────────────────────────────────


class TestFromFileMultiResource:
    def test_loads_specific_resource(self, multi_resource_file):
        ds = Dataset.from_file(multi_resource_file, resource="roads")
        assert ds.dataset_id == "globex_roads"
        assert ds.resource_label == "roads"

    def test_requires_resource_name(self, multi_resource_file):
        with pytest.raises(ValueError, match="Multiple resources"):
            Dataset.from_file(multi_resource_file)

    def test_resource_not_found_raises(self, multi_resource_file):
        with pytest.raises(KeyError, match="nosuch"):
            Dataset.from_file(multi_resource_file, resource="nosuch")


# ── Error cases ──────────────────────────────────────────────────────────────


class TestErrors:
    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            Dataset.from_file(tmp_path / "nonexistent.json")

    def test_empty_resources_no_name(self, empty_resources_file):
        with pytest.raises(ValueError, match="No resources"):
            Dataset.from_file(empty_resources_file)

    def test_empty_resources_with_name(self, empty_resources_file):
        with pytest.raises(KeyError, match="foo"):
            Dataset.from_file(empty_resources_file, resource="foo")

    def test_missing_pipeline_sections_return_empty(self, tmp_path):
        data = {
            "provider": {"label": "bare", "name": "Bare", "url": {}},
            "resources": [{"label": "r", "name": "R"}],
        }
        p = tmp_path / "bare.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        ds = Dataset.from_file(p)
        assert ds.collection == {}
        assert ds.ingestion == {}
        assert ds.matching == {}
        assert ds.license_type == ""


# ── download_url ─────────────────────────────────────────────────────────────


class TestDownloadUrl:
    def test_concatenates_url_and_endpoint(self, tmp_path):
        data = {
            "provider": {"label": "acme", "name": "Acme", "url": {}},
            "resources": [
                {
                    "label": "widgets",
                    "name": "Widgets",
                    "collection": {
                        "data_download": {
                            "type": "http",
                            "url": "https://example.com/",
                            "endpoint": "a/b/",
                        }
                    },
                }
            ],
        }
        p = tmp_path / "acme.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        ds = Dataset.from_file(p)
        assert ds.download_url == "https://example.com/a/b/"

    def test_url_without_endpoint(self, tmp_path):
        data = {
            "provider": {"label": "acme", "name": "Acme", "url": {}},
            "resources": [
                {
                    "label": "widgets",
                    "name": "Widgets",
                    "collection": {
                        "data_download": {
                            "type": "http",
                            "url": "https://example.com/a",
                        }
                    },
                }
            ],
        }
        p = tmp_path / "acme.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        ds = Dataset.from_file(p)
        assert ds.download_url == "https://example.com/a"

    def test_raises_when_missing(self, single_resource_file):
        ds = Dataset.from_file(single_resource_file)
        with pytest.raises(ValueError, match="No data_download"):
            _ = ds.download_url

    def test_download_region(self, tmp_path):
        data = {
            "provider": {"label": "acme", "name": "Acme", "url": {}},
            "resources": [
                {
                    "label": "widgets",
                    "name": "Widgets",
                    "collection": {
                        "data_download": {
                            "type": "s3",
                            "url": "s3://acme/",
                            "region": "eu-central-1",
                        }
                    },
                }
            ],
        }
        p = tmp_path / "acme.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        assert Dataset.from_file(p).download_region == "eu-central-1"

    def test_download_region_none_when_unset(self, single_resource_file):
        assert Dataset.from_file(single_resource_file).download_region is None


# ── from_name / path_for ─────────────────────────────────────────────────────


class TestFromName:
    def test_delegates_to_from_file(self, single_resource_file):
        """from_name builds a path under the given datasets_dir and calls from_file."""
        ds = Dataset.from_name(
            "acme", "widgets", datasets_dir=single_resource_file.parent
        )
        assert ds.dataset_id == "acme_widgets"

    def test_missing_provider_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            Dataset.from_name("nonexistent", "x", datasets_dir=tmp_path)

    def test_path_for_joins_datasets_dir_and_label(self, tmp_path):
        assert Dataset.path_for("acme", tmp_path) == tmp_path / "acme.json"

    def test_path_for_accepts_str_datasets_dir(self, tmp_path):
        assert Dataset.path_for("acme", str(tmp_path)) == tmp_path / "acme.json"


# ── all_from_file ────────────────────────────────────────────────────────────


class TestAllFromFile:
    def test_returns_all_resources(self, multi_resource_file):
        datasets = Dataset.all_from_file(multi_resource_file)
        assert len(datasets) == 2
        labels = {ds.resource_label for ds in datasets}
        assert labels == {"buildings", "roads"}

    def test_empty_resources(self, empty_resources_file):
        datasets = Dataset.all_from_file(empty_resources_file)
        assert datasets == []

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            Dataset.all_from_file(tmp_path / "missing.json")


class TestPackagedDatasets:
    def test_from_name_defaults_to_packaged_dir(self):
        ds = Dataset.from_name("us_dot", "nad")
        assert ds.dataset_id == "us_dot_nad"

    def test_path_for_defaults_to_packaged_dir(self):
        assert Dataset.path_for("osm") == DATASETS_DIR / "osm.json"
        assert Dataset.path_for("osm").is_file()


# ── themes ───────────────────────────────────────────────────────────────────


@pytest.fixture()
def themed_file(tmp_path):
    """File-level themes, with one resource overriding and one inheriting."""
    data = {
        "provider": {"label": "initech", "name": "Initech", "url": {}},
        "themes": ["buildings"],
        "resources": [
            {"label": "inherits", "name": "Inherits"},
            {
                "label": "overrides",
                "name": "Overrides",
                "themes": ["base", "divisions"],
            },
        ],
    }
    p = tmp_path / "initech.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


class TestThemes:
    def test_inherits_file_level(self, themed_file):
        assert Dataset.from_file(themed_file, resource="inherits").themes == [
            "buildings"
        ]

    def test_resource_overrides_file_level(self, themed_file):
        assert Dataset.from_file(themed_file, resource="overrides").themes == [
            "base",
            "divisions",
        ]

    def test_resource_only(self, multi_resource_file):
        data = json.loads(multi_resource_file.read_text(encoding="utf-8"))
        data["resources"][1]["themes"] = ["transportation"]
        multi_resource_file.write_text(json.dumps(data), encoding="utf-8")
        assert Dataset.from_file(multi_resource_file, "roads").themes == [
            "transportation"
        ]
        assert Dataset.from_file(multi_resource_file, "buildings").themes == []

    def test_defaults_to_empty(self, single_resource_file):
        assert Dataset.from_file(single_resource_file).themes == []

    def test_all_from_file_resolves_each_resource(self, themed_file):
        resolved = {
            ds.resource_label: ds.themes for ds in Dataset.all_from_file(themed_file)
        }
        assert resolved == {
            "inherits": ["buildings"],
            "overrides": ["base", "divisions"],
        }

    def test_constructor_dataset_themes(self):
        ds = Dataset(
            {"label": "a"}, {"label": "b"}, dataset_id="a_b", dataset_themes=["base"]
        )
        assert ds.themes == ["base"]

    def test_themes_returns_a_copy(self, themed_file):
        ds = Dataset.from_file(themed_file, resource="overrides")
        ds.themes.append("places")
        assert ds.themes == ["base", "divisions"]


class TestForTheme:
    def test_filters_by_resolved_themes(self, themed_file, single_resource_file):
        directory = themed_file.parent
        assert single_resource_file.parent == directory
        ids = [ds.dataset_id for ds in Dataset.for_theme("buildings", directory)]
        assert ids == ["initech_inherits"]
        ids = [ds.dataset_id for ds in Dataset.for_theme("divisions", directory)]
        assert ids == ["initech_overrides"]
        assert Dataset.for_theme("places", directory) == []

    def test_unknown_theme_raises(self, tmp_path):
        with pytest.raises(ValueError, match="Unknown theme 'roads'"):
            Dataset.for_theme("roads", tmp_path)

    def test_defaults_to_packaged_dir(self):
        ids = {ds.dataset_id for ds in Dataset.for_theme("transportation")}
        assert {"tomtom_orbis", "osm_planet", "us_dot_hpms"} <= ids
        assert "us_dot_nad" not in ids

    @pytest.mark.parametrize(
        "provider, resource, themes",
        [
            ("osm", "planet", ["base", "buildings", "divisions", "transportation"]),
            ("osm", "coastlines", ["base"]),
            ("osm", "planet_history", []),
            ("microsoft", "ml_buildings", ["buildings"]),
            ("microsoft", "maps_entity_variant_names", ["divisions"]),
            ("microsoft", "microsoft", ["places"]),
            ("us_dot", "nad", ["addresses"]),
            ("google", "open_buildings", ["buildings"]),
        ],
    )
    def test_packaged_resolution(self, provider, resource, themes):
        assert Dataset.from_name(provider, resource).themes == themes


# ── delivery ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def delivery_file(tmp_path):
    """File-level delivery, with one resource overriding and one inheriting."""
    data = {
        "provider": {"label": "hooli", "name": "Hooli", "url": {}},
        "delivery": {"method": "bucket", "direction": "pull", "auth": "iam"},
        "resources": [
            {"label": "inherits", "name": "Inherits", "collection": {}},
            {
                "label": "overrides",
                "name": "Overrides",
                "collection": {"delivery": {"trigger": "manual"}},
            },
        ],
    }
    p = tmp_path / "hooli.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


class TestDelivery:
    def test_inherits_file_level(self, delivery_file):
        assert Dataset.from_file(delivery_file, resource="inherits").delivery == {
            "method": "bucket",
            "direction": "pull",
            "auth": "iam",
        }

    def test_resource_replaces_file_level_whole(self, delivery_file):
        assert Dataset.from_file(delivery_file, resource="overrides").delivery == {
            "trigger": "manual"
        }

    def test_all_from_file_resolves_each_resource(self, delivery_file):
        resolved = {
            ds.resource_label: ds.delivery
            for ds in Dataset.all_from_file(delivery_file)
        }
        assert resolved["inherits"]["method"] == "bucket"
        assert resolved["overrides"] == {"trigger": "manual"}

    def test_defaults_to_empty(self, single_resource_file):
        assert Dataset.from_file(single_resource_file).delivery == {}

    def test_returns_a_copy(self, delivery_file):
        ds = Dataset.from_file(delivery_file, resource="inherits")
        ds.delivery["auth"] = "none"
        assert ds.delivery["auth"] == "iam"

    @pytest.mark.parametrize(
        "provider, resource, expected",
        [
            ("open_addresses", "at_countrywide", {"method": "bucket", "auth": "iam"}),
            ("meta", "meta", {"direction": "pull", "formats": ["parquet"]}),
            ("pinmeto", "pinmeto", {"direction": "push", "trigger": "scheduled"}),
            ("osm", "coastlines", {"method": "file_download", "auth": "none"}),
            ("tomtom", "orbis", {"auth": "api_key", "formats": ["osm_pbf"]}),
        ],
    )
    def test_packaged_resolution(self, provider, resource, expected):
        delivery = Dataset.from_name(provider, resource).delivery
        assert {k: delivery[k] for k in expected} == expected
