"""GURS (Slovenia): the download URL comes from a signed-URL API."""

from __future__ import annotations

import datetime

import requests

from overture_dataset_configs.adapters.addresses._versioning import date_version
from overture_dataset_configs.adapters.addresses.base import CollectPlan, HttpSource

_SI_API_URL = "https://ipi.eprostor.gov.si/jgp-service-api/display-views/groups/121/composite-products/141/file?filterParam=DRZAVA&filterValue=1"


class SIResourceConfig(HttpSource):
    name = "gurs"
    provider = "gurs"
    country = "SI"
    url = None

    def __init__(self, api_url: str = _SI_API_URL) -> None:
        self.api_url = api_url

    @classmethod
    def from_dict(cls, d: dict) -> "SIResourceConfig":
        dd = d.get("data_download") or {}
        return cls(api_url=(dd.get("url", "") + dd.get("endpoint", "")) or _SI_API_URL)

    def resolve_url(self) -> str:
        resp = requests.get(self.api_url, timeout=30)
        resp.raise_for_status()
        return resp.json()["url"]

    def plan(self, run_date: datetime.date) -> CollectPlan:
        return CollectPlan(
            "http_signed_api",
            date_version(run_date),
            "source.zip",
            api_url=self.api_url,
        )
