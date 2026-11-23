"""US DOT National Address Database, hosted on Socrata."""

from __future__ import annotations

import datetime

import requests

from overture_dataset_configs.adapters.addresses.base import CollectPlan, HttpSource

_NAD_SOCRATA_API = "https://data.transportation.gov/api/views/fc2s-wawr.json"


class SocrataResourceConfig(HttpSource):
    """Socrata-hosted resource: version from ``viewLastModified`` metadata (no Last-Modified)."""

    name = "nad"
    provider = "us_dot"
    country = "US"
    url = None
    filename = "source.zip"

    def __init__(
        self,
        download_url: str,
        socrata_api: str = _NAD_SOCRATA_API,
    ) -> None:
        self.download_url = download_url
        self.socrata_api = socrata_api

    @classmethod
    def from_dict(cls, d: dict) -> "SocrataResourceConfig":
        dd = d["data_download"]
        return cls(
            download_url=dd["url"] + dd.get("endpoint", ""),
            socrata_api=(d.get("api") or {}).get("url", _NAD_SOCRATA_API),
        )

    def _resolve(self) -> tuple[str, str]:
        resp = requests.get(self.socrata_api, timeout=30)
        resp.raise_for_status()
        meta = resp.json()
        # NAD is a file ("blobby") asset: rowsUpdatedAt is fixed at creation and
        # never changes when a new file is uploaded, but viewLastModified does.
        updated_at = meta.get("viewLastModified") or meta["rowsUpdatedAt"]
        version = datetime.datetime.fromtimestamp(
            updated_at, tz=datetime.timezone.utc
        ).strftime("%Y%m%d")
        return self.download_url, version

    def plan(self, run_date: datetime.date) -> CollectPlan:
        url, version = self._resolve()
        return self._download_plan(url, version)
