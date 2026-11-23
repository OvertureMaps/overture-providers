"""Tests for addresses collect — OA and HTTP providers."""

import datetime
import json
from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import HTTPError

from overture_dataset_configs.adapters.addresses.collect import fetch_all_oa_jobs
from overture_dataset_configs.adapters.addresses.loaders import (
    load_http_resources,
    load_oa_resources,
)
from overture_dataset_configs.adapters.addresses import (
    CollectPlan,
    CZResourceConfig,
    HttpHeadProbeConfig,
    HttpResourceConfig,
    HttpSource,
    OAResourceConfig,
    SIResourceConfig,
    SocrataResourceConfig,
)
from overture_dataset_configs.dataset import Dataset
from overture_dataset_configs.dataset import DATASETS_DIR


OA_API_RESPONSE = [
    {"source": "at/countrywide", "job": 834288},
    {"source": "us/ca/statewide", "job": 901234},
    {"source": "gb/countrywide", "job": 777001},
]

# Fixed "today" for CZ tests: 2026-05-15 → last day of April = 2026-04-30
_TODAY = datetime.date(2026, 5, 15)
_APRIL_URL = "https://vdp.cuzk.gov.cz/vymenny_format/csv/20260430_OB_ADR_csv.zip"
_MARCH_URL = "https://vdp.cuzk.gov.cz/vymenny_format/csv/20260331_OB_ADR_csv.zip"
_FEB_URL = "https://vdp.cuzk.gov.cz/vymenny_format/csv/20260228_OB_ADR_csv.zip"


def _mock_datetime(fixed_today: datetime.date):
    """Patch target for a module's `datetime`.

    Returns a stand-in that pins date.today() while forwarding date(y, m, d)
    calls and timedelta to the real implementations.
    """

    class _MockDate:
        @staticmethod
        def today() -> datetime.date:
            return fixed_today

        def __new__(cls, *args, **kwargs):
            return datetime.date(*args, **kwargs)

    class _MockDatetime:
        date = _MockDate
        timedelta = datetime.timedelta

    return _MockDatetime


def _get_response(json_data=None, status_code=200):
    """Build a mock requests.get response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    if status_code >= 400:
        resp.raise_for_status.side_effect = HTTPError(f"HTTP {status_code}")
    else:
        resp.raise_for_status.return_value = None
    return resp


def _head_response(status_code=200, headers=None):
    """Build a mock requests.head response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = headers or {}
    return resp


# ── OA API ────────────────────────────────────────────────────────────────────


class TestFetchAllOaJobs:
    _PATCH = "overture_dataset_configs.adapters.addresses.collect.requests.get"

    _API_BASE = "https://batch.openaddresses.io/api"

    def test_requests_addresses_layer(self):
        mock_resp = _get_response(json_data=OA_API_RESPONSE)
        with patch(self._PATCH, return_value=mock_resp) as mock_get:
            fetch_all_oa_jobs(self._API_BASE)
        assert mock_get.call_args.kwargs.get("params") == {"layer": "addresses"}

    def test_returns_source_to_job_mapping(self):
        mock_resp = _get_response(json_data=OA_API_RESPONSE)
        with patch(self._PATCH, return_value=mock_resp):
            result = fetch_all_oa_jobs(self._API_BASE)
        assert result == {
            "at/countrywide": 834288,
            "us/ca/statewide": 901234,
            "gb/countrywide": 777001,
        }

    def test_raises_on_http_error(self):
        mock_resp = _get_response(status_code=500)
        with patch(self._PATCH, return_value=mock_resp):
            with pytest.raises(Exception):
                fetch_all_oa_jobs(self._API_BASE)


# ── OAResourceConfig ──────────────────────────────────────────────────────────


_OA_BATCH_DEFAULTS = {
    "batch_api": "https://batch.openaddresses.io/api",
    "batch_bucket": "v2.openaddresses.io",
}


def _oa_from_dict(**overrides) -> OAResourceConfig:
    return OAResourceConfig.from_dict({**_OA_BATCH_DEFAULTS, **overrides})


class TestOAResourceConfig:
    def test_from_dict_minimal(self):
        r = _oa_from_dict(source="at/countrywide")
        assert r.source == "at/countrywide"
        assert r.batch_api == "https://batch.openaddresses.io/api"
        assert r.batch_bucket == "v2.openaddresses.io"
        assert r.label is None
        assert r.handler is None
        assert r.subdivision_code is None
        assert r.address_level_fields == []
        assert r.dataset is None

    def test_from_dict_full(self):
        r = _oa_from_dict(
            source="ca/qc/province",
            handler="CAQCDataset",
            subdivision_code="QC",
            address_level_fields=["street", "city"],
            dataset="qc_addr",
        )
        assert r.handler == "CAQCDataset"
        assert r.subdivision_code == "QC"
        assert r.address_level_fields == ["street", "city"]
        assert r.dataset == "qc_addr"

    def test_defaults_merge(self):
        r = _oa_from_dict(source="ca/bc/province", handler="CADataset")
        assert r.handler == "CADataset"

    def test_source_overrides_default(self):
        r = _oa_from_dict(source="ca/qc/province", handler="CAQCDataset")
        assert r.handler == "CAQCDataset"

    def test_country_property(self):
        assert _oa_from_dict(source="ca/qc/province").country == "CA"
        assert _oa_from_dict(source="us/ca/alameda").country == "US"


# ── load_oa_resources ─────────────────────────────────────────────────────────


def _oa_resource(label: str, source: str, iso_3166_2: str | None = None) -> dict:
    area = {"iso_3166_1": source.split("/")[0].upper()}
    if iso_3166_2:
        area["iso_3166_2"] = iso_3166_2
    return {
        "label": label,
        "name": source,
        "collection": {
            "coverage": {"areas": [area], "description": ""},
            "api": {"url": "https://batch.openaddresses.io/api"},
            "extras": {
                "batch_bucket": "v2.openaddresses.io",
                "oa_batch_source": source,
            },
        },
        "ingestion": {},
        "matching": {},
    }


_OA_JSON = json.dumps(
    {
        "provider": {
            "label": "open_addresses",
            "name": "OpenAddresses",
            "url": {},
        },
        "resources": [
            _oa_resource("at_countrywide", "at/countrywide"),
            _oa_resource("ca_countrywide", "ca/countrywide"),
            _oa_resource("us_ny_city_of_new_york", "us/ny/city_of_new_york", "US-NY"),
        ],
    }
)

_NON_OA_JSON = json.dumps(
    {
        "provider": {"label": "some_other_provider", "name": "Other", "url": {}},
        "resources": [
            {
                "label": "x",
                "name": "X",
                "collection": {
                    "data_download": {
                        "type": "http",
                        "url": "https://example.com/data.zip",
                    },
                    "coverage": {"areas": [{"iso_3166_1": "XX"}], "description": ""},
                },
                "ingestion": {},
                "matching": {},
            }
        ],
    }
)


class TestLoadOaResources:
    def _oa_datasets(self, tmp_path) -> list[Dataset]:
        f = tmp_path / "open_addresses.json"
        f.write_text(_OA_JSON)
        return Dataset.all_from_file(f)

    def _non_oa_datasets(self, tmp_path) -> list[Dataset]:
        f = tmp_path / "some_other.json"
        f.write_text(_NON_OA_JSON)
        return Dataset.all_from_file(f)

    def test_returns_one_config_per_resource(self, tmp_path):
        resources = load_oa_resources(self._oa_datasets(tmp_path))
        assert [r.source for r in resources] == [
            "at/countrywide",
            "ca/countrywide",
            "us/ny/city_of_new_york",
        ]

    def test_us_subdivision_derived_from_iso_3166_2(self, tmp_path):
        resources = load_oa_resources(self._oa_datasets(tmp_path))
        us = next(r for r in resources if r.source == "us/ny/city_of_new_york")
        assert us.subdivision_code == "NY"

    def test_non_us_subdivision_is_none(self, tmp_path):
        resources = load_oa_resources(self._oa_datasets(tmp_path))
        ca = next(r for r in resources if r.source == "ca/countrywide")
        assert ca.subdivision_code is None

    def test_skips_non_open_addresses_provider(self, tmp_path):
        datasets = self._oa_datasets(tmp_path) + self._non_oa_datasets(tmp_path)
        resources = load_oa_resources(datasets)
        assert len(resources) == 3  # only the 3 OA resources

    def test_label_is_canonical_resource_label(self, tmp_path):
        resources = load_oa_resources(self._oa_datasets(tmp_path))
        assert [r.label for r in resources] == [
            "at_countrywide",
            "ca_countrywide",
            "us_ny_city_of_new_york",
        ]

    def test_dataset_carries_per_resource_name(self, tmp_path):
        resources = load_oa_resources(self._oa_datasets(tmp_path))
        assert [r.dataset for r in resources] == [
            "at/countrywide",
            "ca/countrywide",
            "us/ny/city_of_new_york",
        ]


# ── ČÚZK HEAD probe ───────────────────────────────────────────────────────────


class TestCZResourceConfig:
    _PATCH = "overture_dataset_configs.adapters.addresses.cuzk.requests.head"

    def _cz(self) -> CZResourceConfig:
        return CZResourceConfig()

    def test_probes_last_day_of_previous_month_first(self):
        mock_resp = _head_response(
            200, {"Last-Modified": "Fri, 01 May 2026 05:00:00 GMT"}
        )
        with patch(self._PATCH, return_value=mock_resp):
            with patch(
                "overture_dataset_configs.adapters.addresses.cuzk.datetime",
                _mock_datetime(_TODAY),
            ):
                url, _ = self._cz()._resolve()
        assert url == _APRIL_URL

    def test_version_from_last_modified_header(self):
        mock_resp = _head_response(
            200, {"Last-Modified": "Fri, 01 May 2026 05:00:00 GMT"}
        )
        with patch(self._PATCH, return_value=mock_resp):
            with patch(
                "overture_dataset_configs.adapters.addresses.cuzk.datetime",
                _mock_datetime(_TODAY),
            ):
                version = self._cz().resolve_version({})
        assert version == "20260501"

    def test_version_falls_back_to_url_date_when_no_last_modified(self):
        mock_resp = _head_response(200, {})
        with patch(self._PATCH, return_value=mock_resp):
            with patch(
                "overture_dataset_configs.adapters.addresses.cuzk.datetime",
                _mock_datetime(_TODAY),
            ):
                version = self._cz().resolve_version({})
        assert version == "20260430"

    def test_resolve_url_returns_probed_url(self):
        mock_resp = _head_response(
            200, {"Last-Modified": "Fri, 01 May 2026 05:00:00 GMT"}
        )
        with patch(self._PATCH, return_value=mock_resp):
            with patch(
                "overture_dataset_configs.adapters.addresses.cuzk.datetime",
                _mock_datetime(_TODAY),
            ):
                assert self._cz().resolve_url() == _APRIL_URL

    def test_falls_back_to_previous_month_on_404(self):
        responses = [
            _head_response(404),
            _head_response(200, {"Last-Modified": "Wed, 01 Apr 2026 05:00:00 GMT"}),
        ]
        with patch(self._PATCH, side_effect=responses):
            with patch(
                "overture_dataset_configs.adapters.addresses.cuzk.datetime",
                _mock_datetime(_TODAY),
            ):
                url, version = self._cz()._resolve()
        assert url == _MARCH_URL
        assert version == "20260401"

    def test_raises_after_three_consecutive_failures(self):
        responses = [_head_response(404)] * 3
        with patch(self._PATCH, side_effect=responses):
            with patch(
                "overture_dataset_configs.adapters.addresses.cuzk.datetime",
                _mock_datetime(_TODAY),
            ):
                with pytest.raises(RuntimeError, match="3 months"):
                    self._cz()._resolve()


# ── HTTP base config ──────────────────────────────────────────────────────────


class TestHttpResourceConfigResolveVersion:
    def test_defaults_to_dag_execution_date(self):
        r = HttpResourceConfig(
            name="example",
            url="https://example.com/data.zip",
            provider="example",
            country="US",
        )
        assert r.resolve_version({"ds": "2026-05-15"}) == "2026-05-15"

    def test_from_dict(self):
        r = HttpResourceConfig.from_dict(
            {
                "name": "bag_light",
                "url": "https://example.com/bag.gpkg",
                "provider": "pdok",
                "country": "NL",
            }
        )
        assert r.name == "bag_light"
        assert r.provider == "pdok"
        assert r.subdivision is None


# ── load_http_resources ───────────────────────────────────────────────────────


_HTTP_STATIC_JSON = json.dumps(
    {
        "provider": {
            "label": "byggoastofnun",
            "name": "Byggðastofnun",
            "url": {},
        },
        "resources": [
            {
                "label": "byggoastofnun",
                "name": "Byggðastofnun",
                "collection": {
                    "data_download": {
                        "type": "http",
                        "url": "https://example.com/byggoastofnun.gpkg",
                    },
                    "coverage": {"areas": [{"iso_3166_1": "IS"}]},
                },
                "ingestion": {},
                "matching": {},
            }
        ],
    }
)

_HTTP_STATIC_WITH_SUBDIVISION_JSON = json.dumps(
    {
        "provider": {
            "label": "nyc_dcp",
            "name": "NYC DCP",
            "url": {},
        },
        "resources": [
            {
                "label": "test_resource",
                "name": "Test Resource",
                "collection": {
                    "data_download": {
                        "type": "http",
                        "url": "https://example.com/data.zip",
                    },
                    "coverage": {
                        "areas": [{"iso_3166_1": "US", "iso_3166_2": ["US-NY"]}]
                    },
                },
                "ingestion": {},
                "matching": {},
            }
        ],
    }
)

_HTTP_MONTHLY_PROBE_JSON = json.dumps(
    {
        "provider": {
            "label": "cuzk",
            "name": "ČÚZK",
            "url": {},
        },
        "resources": [
            {
                "label": "cuzk",
                "name": "ČÚZK",
                "collection": {
                    "data_download": {
                        "type": "http",
                        "url": "https://example.com/{date}_data.zip",
                    },
                },
                "ingestion": {},
                "matching": {},
            }
        ],
    }
)

_HTTP_SIGNED_API_JSON = json.dumps(
    {
        "provider": {
            "label": "gurs",
            "name": "GURS",
            "url": {},
        },
        "resources": [
            {
                "label": "gurs",
                "name": "GURS",
                "collection": {
                    "data_download": {
                        "type": "http",
                        "url": "https://example.com/signed-api",
                    },
                },
                "ingestion": {},
                "matching": {},
            }
        ],
    }
)


class TestLoadHttpResources:
    def _datasets(self, tmp_path, label: str, content: str) -> list[Dataset]:
        f = tmp_path / f"{label}.json"
        f.write_text(content)
        return Dataset.all_from_file(f)

    def test_http_static_returns_http_resource_config(self, tmp_path):
        datasets = self._datasets(tmp_path, "byggoastofnun", _HTTP_STATIC_JSON)
        results = load_http_resources(datasets)
        assert len(results) == 1
        assert isinstance(results[0], HttpResourceConfig)

    def test_http_static_reads_url_and_country(self, tmp_path):
        datasets = self._datasets(tmp_path, "byggoastofnun", _HTTP_STATIC_JSON)
        r = load_http_resources(datasets)[0]
        assert r.url == "https://example.com/byggoastofnun.gpkg"
        assert r.country == "IS"
        assert r.provider == "byggoastofnun"
        assert r.name == "byggoastofnun"

    def test_http_static_subdivision_from_list(self, tmp_path):
        datasets = self._datasets(
            tmp_path, "nyc_dcp", _HTTP_STATIC_WITH_SUBDIVISION_JSON
        )
        r = load_http_resources(datasets)[0]
        assert r.subdivision == "US-NY"

    def test_packaged_nyc_dcp_subdivision_from_string(self):
        datasets = Dataset.all_from_file(Dataset.path_for("nyc_dcp", DATASETS_DIR))
        assert datasets[0].coverage["areas"][0]["iso_3166_2"] == "US-NY"
        r = load_http_resources(datasets)[0]
        assert r.subdivision == "US-NY"

    def test_http_static_no_subdivision(self, tmp_path):
        datasets = self._datasets(tmp_path, "byggoastofnun", _HTTP_STATIC_JSON)
        r = load_http_resources(datasets)[0]
        assert r.subdivision is None

    def test_http_monthly_probe_returns_cz_config(self, tmp_path):
        datasets = self._datasets(tmp_path, "cuzk", _HTTP_MONTHLY_PROBE_JSON)
        results = load_http_resources(datasets)
        assert len(results) == 1
        assert isinstance(results[0], CZResourceConfig)

    def test_http_monthly_probe_uses_url_template(self, tmp_path):
        datasets = self._datasets(tmp_path, "cuzk", _HTTP_MONTHLY_PROBE_JSON)
        r = load_http_resources(datasets)[0]
        assert r.url_template == "https://example.com/{date}_data.zip"

    def test_http_signed_api_returns_si_config(self, tmp_path):
        datasets = self._datasets(tmp_path, "gurs", _HTTP_SIGNED_API_JSON)
        results = load_http_resources(datasets)
        assert len(results) == 1
        assert isinstance(results[0], SIResourceConfig)

    def test_http_signed_api_uses_url(self, tmp_path):
        datasets = self._datasets(tmp_path, "gurs", _HTTP_SIGNED_API_JSON)
        r = load_http_resources(datasets)[0]
        assert r.api_url == "https://example.com/signed-api"

    def test_skips_unregistered_provider(self, tmp_path):
        unregistered = json.dumps(
            {
                "provider": {"label": "x", "name": "X", "url": {}},
                "resources": [
                    {
                        "label": "x",
                        "name": "X",
                        "collection": {
                            "data_download": {
                                "type": "http",
                                "url": "https://example.com/data.zip",
                            },
                            "coverage": {"areas": [{"iso_3166_1": "XX"}]},
                        },
                        "ingestion": {},
                        "matching": {},
                    }
                ],
            }
        )
        datasets = self._datasets(tmp_path, "x", unregistered)
        assert load_http_resources(datasets) == []

    def test_us_dot_config_loads_nad_as_socrata_and_skips_hpms(self):
        # The collect DAG builds task IDs and S3 paths from r.provider/r.name, which
        # SocrataResourceConfig hardcodes; they must match the dataset labels.
        datasets = Dataset.all_from_file(Dataset.path_for("us_dot", DATASETS_DIR))
        assert {d.resource_label for d in datasets} == {"hpms", "nad"}
        results = load_http_resources(datasets)
        assert len(results) == 1
        r = results[0]
        assert isinstance(r, SocrataResourceConfig)
        assert (r.provider, r.name) == ("us_dot", "nad")
        assert (
            r.socrata_api == "https://data.transportation.gov/api/views/fc2s-wawr.json"
        )


# ── SIResourceConfig ──────────────────────────────────────────────────────────


class TestSIResourceConfig:
    _PATCH = "overture_dataset_configs.adapters.addresses.gurs.requests.get"
    _API_URL = "https://example.com/signed-api"

    def _si(self) -> SIResourceConfig:
        return SIResourceConfig(api_url=self._API_URL)

    def test_from_dict_uses_url(self):
        r = SIResourceConfig.from_dict(
            {"data_download": {"type": "http", "url": "https://custom.example.com/api"}}
        )
        assert r.api_url == "https://custom.example.com/api"

    def test_from_dict_falls_back_to_default(self):
        r = SIResourceConfig.from_dict({})
        from overture_dataset_configs.adapters.addresses.gurs import (
            _SI_API_URL,
        )

        assert r.api_url == _SI_API_URL

    def test_resolve_url_returns_json_url(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "url": "https://signed.example.com/download?token=abc"
        }
        with patch(self._PATCH, return_value=mock_resp):
            result = self._si().resolve_url()
        assert result == "https://signed.example.com/download?token=abc"

    def test_resolve_url_raises_on_http_error(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = HTTPError("HTTP 403")
        with patch(self._PATCH, return_value=mock_resp):
            with pytest.raises(HTTPError):
                self._si().resolve_url()


# ── HttpHeadProbeConfig ───────────────────────────────────────────────────────


_HTTP_HEAD_PROBE_JSON = json.dumps(
    {
        "provider": {
            "label": "pdok",
            "name": "PDOK",
            "url": {},
        },
        "resources": [
            {
                "label": "bag_light",
                "name": "BAG Light",
                "collection": {
                    "data_download": {
                        "type": "http",
                        "url": "https://example.com/bag.gpkg",
                    },
                    "coverage": {"areas": [{"iso_3166_1": "NL"}]},
                },
                "ingestion": {},
                "matching": {},
            }
        ],
    }
)


class TestHttpHeadProbeConfig:
    _PATCH = "overture_dataset_configs.adapters.addresses.strategies.requests.head"
    _URL = "https://example.com/bag.gpkg"

    def _probe(self) -> HttpHeadProbeConfig:
        return HttpHeadProbeConfig(
            name="bag_light",
            provider="pdok",
            country="NL",
            download_url=self._URL,
        )

    def test_url_is_none(self):
        assert self._probe().url is None

    def test_resolve_returns_url_and_version_from_last_modified(self):
        mock_resp = _head_response(
            200, {"Last-Modified": "Mon, 01 Jan 2026 00:00:00 GMT"}
        )
        with patch(self._PATCH, return_value=mock_resp):
            url, version = self._probe()._resolve()
        assert url == self._URL
        assert version == "20260101"

    def test_resolve_falls_back_to_today_when_no_last_modified(self):
        mock_resp = _head_response(200, {})
        with patch(self._PATCH, return_value=mock_resp):
            with patch(
                "overture_dataset_configs.adapters.addresses.strategies.datetime",
                _mock_datetime(_TODAY),
            ):
                _, version = self._probe()._resolve()
        assert version == _TODAY.strftime("%Y%m%d")

    def test_resolve_raises_on_http_error(self):
        mock_resp = _head_response(404)
        mock_resp.raise_for_status.side_effect = HTTPError("HTTP 404")
        with patch(self._PATCH, return_value=mock_resp):
            with pytest.raises(HTTPError):
                self._probe()._resolve()


class TestLoadHttpResourcesHeadProbe:
    def _datasets(self, tmp_path) -> list[Dataset]:
        f = tmp_path / "pdok.json"
        f.write_text(_HTTP_HEAD_PROBE_JSON)
        return Dataset.all_from_file(f)

    def test_http_head_probe_returns_head_probe_config(self, tmp_path):
        results = load_http_resources(self._datasets(tmp_path))
        assert len(results) == 1
        assert isinstance(results[0], HttpHeadProbeConfig)

    def test_http_head_probe_reads_url_and_country(self, tmp_path):
        r = load_http_resources(self._datasets(tmp_path))[0]
        assert r.download_url == "https://example.com/bag.gpkg"
        assert r.country == "NL"
        assert r.provider == "pdok"
        assert r.name == "bag_light"
        assert r.url is None


# ── SocrataResourceConfig (http_socrata → USDOT NAD) ──────────────────────────


class TestSocrataResourceConfig:
    _PATCH = "overture_dataset_configs.adapters.addresses.us_dot_nad.requests.get"
    _DOWNLOAD_URL = "https://data.transportation.gov/download/fc2s-wawr/application%2Fx-zip-compressed"
    _SOCRATA_API = "https://data.transportation.gov/api/views/fc2s-wawr.json"

    def _cfg(self) -> SocrataResourceConfig:
        return SocrataResourceConfig(
            download_url=self._DOWNLOAD_URL, socrata_api=self._SOCRATA_API
        )

    def test_from_dict(self):
        cfg = SocrataResourceConfig.from_dict(
            {
                "data_download": {"type": "http", "url": self._DOWNLOAD_URL},
                "socrata_api": self._SOCRATA_API,
            }
        )
        assert cfg.download_url == self._DOWNLOAD_URL
        assert cfg.socrata_api == self._SOCRATA_API

    def test_from_dict_defaults_socrata_api(self):
        cfg = SocrataResourceConfig.from_dict(
            {"data_download": {"type": "http", "url": self._DOWNLOAD_URL}}
        )
        # Default falls back to the NAD Socrata endpoint constant.
        assert "data.transportation.gov" in cfg.socrata_api

    def test_resolve_returns_download_url_unchanged(self):
        # Version derives from rowsUpdatedAt (2025-09-24 UTC).
        mock_resp = _get_response(json_data={"rowsUpdatedAt": 1758735232})
        with patch(self._PATCH, return_value=mock_resp):
            url, version = self._cfg()._resolve()
        assert url == self._DOWNLOAD_URL
        assert version == "20250924"

    def test_resolve_prefers_view_last_modified(self):
        # File ("blobby") assets keep rowsUpdatedAt at creation time
        # (2025-09-24); viewLastModified moves on re-upload (2026-09-30).
        mock_resp = _get_response(
            json_data={"rowsUpdatedAt": 1758735232, "viewLastModified": 1790803162}
        )
        with patch(self._PATCH, return_value=mock_resp):
            _, version = self._cfg()._resolve()
        assert version == "20260930"

    def test_resolve_does_not_fetch_download_url(self):
        # The simplified resolver only hits the metadata endpoint; the download
        # URL is used as-is and the 302 redirect is followed at download time
        # by CollectionJob, not pre-resolved here.
        mock_resp = _get_response(json_data={"rowsUpdatedAt": 1758735232})
        with patch(self._PATCH, return_value=mock_resp) as mock_get:
            self._cfg()._resolve()
        assert mock_get.call_count == 1
        assert mock_get.call_args.args[0] == self._SOCRATA_API

    def test_resolve_raises_on_http_error(self):
        mock_resp = _get_response(status_code=500)
        with patch(self._PATCH, return_value=mock_resp):
            with pytest.raises(HTTPError):
                self._cfg()._resolve()


# ── Module-level behaviour introduced by the move ─────────────────────────────


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("Sat, 01 Mar 2025 12:00:00 GMT", "20250301"),
        ("Tue, 31 Dec 2024 23:59:59 GMT", "20241231"),
        ("Wed, 01 Jan 2025 01:00:00 +0200", "20241231"),
    ],
)
def test_parse_http_last_modified_version(header, expected):
    from overture_dataset_configs.adapters.addresses._versioning import (
        parse_http_last_modified_version,
    )

    assert parse_http_last_modified_version(header) == expected


# ── HttpSource.plan ───────────────────────────────────────────────────────────


_RUN_DATE = datetime.date(2026, 5, 15)
_B = "overture_dataset_configs.adapters.addresses"


class TestPlan:
    def test_every_registered_loader_is_a_concrete_http_source(self):
        import inspect

        from overture_dataset_configs.adapters.addresses import loaders

        registered = {
            *loaders._HTTP_LOADER_BY_PROVIDER.values(),
            *loaders._HTTP_LOADER_BY_RESOURCE.values(),
        }
        for cls in registered:
            assert issubclass(cls, HttpSource) and not inspect.isabstract(cls), cls

    def test_static_uses_run_date_and_url_basename(self):
        r = HttpResourceConfig("x", "https://example.com/a.gpkg", "p", "IS")
        assert r.plan(_RUN_DATE) == CollectPlan(
            "http_download",
            "2026-05-15",
            "a.gpkg",
            url="https://example.com/a.gpkg",
        )

    def test_zip_url_lands_as_source_zip(self):
        r = HttpResourceConfig("x", "https://example.com/A.ZIP", "p", "IS")
        assert r.plan(_RUN_DATE).filename == "source.zip"

    def test_head_probe_uses_last_modified(self):
        r = HttpHeadProbeConfig("bag", "pdok", "NL", "https://example.com/bag.gpkg")
        resp = _head_response(200, {"Last-Modified": "Mon, 01 Jan 2026 00:00:00 GMT"})
        with patch(f"{_B}.strategies.requests.head", return_value=resp):
            plan = r.plan(_RUN_DATE)
        assert (plan.url, plan.version, plan.filename) == (
            "https://example.com/bag.gpkg",
            "20260101",
            "bag.gpkg",
        )

    def test_cz_plans_probed_archive(self):
        resp = _head_response(200, {"Last-Modified": "Fri, 01 May 2026 05:00:00 GMT"})
        with patch(f"{_B}.cuzk.requests.head", return_value=resp):
            with patch(f"{_B}.cuzk.datetime", _mock_datetime(_TODAY)):
                plan = CZResourceConfig().plan(_RUN_DATE)
        assert plan == CollectPlan(
            "http_download", "20260501", "source.zip", url=_APRIL_URL
        )

    def test_socrata_lands_as_source_zip(self):
        r = SocrataResourceConfig("https://example.com/download/x")
        resp = _get_response(json_data={"viewLastModified": 1790803162})
        with patch(f"{_B}.us_dot_nad.requests.get", return_value=resp):
            plan = r.plan(_RUN_DATE)
        assert (plan.version, plan.filename) == ("20260930", "source.zip")

    def test_gurs_defers_signed_url_to_collect_job(self):
        with patch(f"{_B}.gurs.requests.get") as mock_get:
            plan = SIResourceConfig(api_url="https://example.com/signed").plan(
                _RUN_DATE
            )
        mock_get.assert_not_called()
        assert plan == CollectPlan(
            "http_signed_api",
            "2026-05-15",
            "source.zip",
            api_url="https://example.com/signed",
        )
