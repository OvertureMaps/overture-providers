"""Semantic checks beyond the structural schema in overture-core."""

import re
from collections import Counter

import pytest
from license_expression import get_spdx_licensing
from overture_dataset_configs import load_config, provider_names

ARCHIVE_PREFIX = "https://web.archive.org/web/"

# Known data defects: archive link is a copy of the primary URL.
ARCHIVE_EXCEPTIONS = {("open_addresses", "de_sl_statewide", "data_location")}

# SPDX licenses whose attribution requirement is fixed by the license text.
ATTRIBUTION_REQUIRED = {
    "CC-BY-4.0": True,
    "ODbL-1.0": True,
    "CDLA-Permissive-2.0": True,
    "Apache-2.0": True,
    "etalab-2.0": True,
    "DL-DE-BY-2.0": True,
    "CC0-1.0": False,
    "PDDL-1.0": False,
    "DL-DE-ZERO-2.0": False,
}

SPDX = get_spdx_licensing()


def _resources():
    for name in provider_names():
        for resource in load_config(name)["resources"]:
            yield name, resource


def _url_pairs(provider, resource):
    collection = resource["collection"]
    yield "data_location", collection["data_location"]
    if collection["license"]:
        yield "license", collection["license"]["url"]


RESOURCES = list(_resources())
IDS = [f"{p}_{r['label']}" for p, r in RESOURCES]


def test_dataset_ids_unique():
    dupes = [i for i, n in Counter(IDS).items() if n > 1]
    assert not dupes


@pytest.mark.parametrize(("provider", "resource"), RESOURCES, ids=IDS)
def test_url_pairs(provider, resource):
    for field, pair in _url_pairs(provider, resource):
        primary, archive = pair["primary"], pair["archive"]
        assert not primary or re.match(r"https?://\S+$", primary), (field, primary)
        if archive and (provider, resource["label"], field) not in ARCHIVE_EXCEPTIONS:
            assert archive.startswith(ARCHIVE_PREFIX), (field, archive)
            assert primary, f"{field}: archive set without primary"


def test_archive_exceptions_still_needed():
    stale = []
    for provider, label, field in ARCHIVE_EXCEPTIONS:
        resource = next(r for p, r in RESOURCES if (p, r["label"]) == (provider, label))
        if resource["collection"][field]["archive"].startswith(ARCHIVE_PREFIX):
            stale.append((provider, label, field))
    assert not stale, "remove fixed entries from ARCHIVE_EXCEPTIONS"


@pytest.mark.parametrize(("provider", "resource"), RESOURCES, ids=IDS)
def test_license_type_is_spdx_or_licenseref(provider, resource):
    license_ = resource["collection"]["license"]
    if license_ is None:
        pytest.skip("no license")
    kind = license_["type"]
    if kind.startswith("LicenseRef-"):
        assert re.fullmatch(r"LicenseRef-[A-Za-z0-9.-]+", kind)
    else:
        info = SPDX.validate(kind)
        assert not info.errors and not info.invalid_symbols, kind


@pytest.mark.parametrize(("provider", "resource"), RESOURCES, ids=IDS)
def test_attribution_matches_license(provider, resource):
    license_ = resource["collection"]["license"]
    expected = ATTRIBUTION_REQUIRED.get(license_ and license_["type"])
    if expected is not None:
        assert license_["requires_attribution"] is expected


@pytest.mark.parametrize(("provider", "resource"), RESOURCES, ids=IDS)
def test_subdivision_matches_country(provider, resource):
    for area in resource["collection"]["coverage"]["areas"]:
        subdivision = area.get("iso_3166_2")
        if subdivision:
            assert subdivision.startswith(area["iso_3166_1"] + "-")
