"""ČÚZK (Czechia): monthly files probed backwards from the end of last month."""

from __future__ import annotations

import datetime

import requests

from overture_dataset_configs.adapters.addresses.base import CollectPlan, HttpSource

from overture_dataset_configs.adapters.addresses._versioning import (
    parse_http_last_modified_version,
)

_CZ_URL_TEMPLATE = "https://vdp.cuzk.gov.cz/vymenny_format/csv/{date}_OB_ADR_csv.zip"


class CZResourceConfig(HttpSource):
    name = "cuzk"
    provider = "cuzk"
    country = "CZ"
    url = None

    def __init__(self, url_template: str = _CZ_URL_TEMPLATE) -> None:
        self.url_template = url_template

    @classmethod
    def from_dict(cls, d: dict) -> "CZResourceConfig":
        dd = d.get("data_download") or {}
        return cls(
            url_template=(dd.get("url", "") + dd.get("endpoint", ""))
            or _CZ_URL_TEMPLATE
        )

    def _resolve(self) -> tuple[str, str]:
        candidate = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
        for _ in range(3):
            url = self.url_template.format(date=candidate.strftime("%Y%m%d"))
            resp = requests.head(url, timeout=10)
            if resp.status_code == 200:
                last_modified = resp.headers.get("Last-Modified", "")
                version = (
                    parse_http_last_modified_version(last_modified)
                    if last_modified
                    else candidate.strftime("%Y%m%d")
                )
                return url, version
            # ČÚZK answers 404 for a month not yet published; anything else is a
            # failure to retry, not a reason to fall back to an older file.
            if resp.status_code != 404:
                resp.raise_for_status()
                raise RuntimeError(
                    f"ČÚZK: unexpected HTTP {resp.status_code} for {url}"
                )
            candidate = candidate.replace(day=1) - datetime.timedelta(days=1)
        raise RuntimeError("ČÚZK: no published file found in the last 3 months")

    def resolve_url(self) -> str:
        url, _ = self._resolve()
        return url

    def resolve_version(self, _context: dict) -> str:
        _, version = self._resolve()
        return version

    def plan(self, run_date: datetime.date) -> CollectPlan:
        url, version = self._resolve()
        return self._download_plan(url, version)
