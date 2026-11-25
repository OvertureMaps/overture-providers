"""Fetch strategies shared by more than one address provider."""

from __future__ import annotations

import datetime
from typing import Optional
from urllib.parse import urlparse, parse_qs

import requests

from overture_dataset_configs.adapters.addresses.base import CollectPlan, HttpSource

from overture_dataset_configs.adapters.addresses._versioning import (
    date_version,
    parse_http_last_modified_version,
)


class OAResourceConfig:
    def __init__(
        self,
        source: str,
        batch_api: str,
        batch_bucket: str,
        label: Optional[str] = None,
        handler: Optional[str] = None,
        subdivision_code: Optional[str] = None,
        address_level_fields: Optional[list[str]] = None,
        dataset: Optional[str] = None,
    ) -> None:
        self.source = source
        self.batch_api = batch_api
        self.batch_bucket = batch_bucket
        self.label = label
        self.handler = handler
        self._subdivision_code = subdivision_code
        self.address_level_fields = address_level_fields or []
        self.dataset = dataset

    @classmethod
    def from_dict(cls, d: dict) -> "OAResourceConfig":
        return cls(
            source=d["source"],
            batch_api=d["batch_api"],
            batch_bucket=d["batch_bucket"],
            label=d.get("label"),
            handler=d.get("handler"),
            subdivision_code=d.get("subdivision_code"),
            address_level_fields=d.get("address_level_fields", []),
            dataset=d.get("dataset"),
        )

    @property
    def country(self) -> str:
        return self.source.split("/")[0].upper()

    @property
    def subdivision_code(self) -> Optional[str]:
        return self._subdivision_code


class HttpResourceConfig(HttpSource):
    def __init__(
        self,
        name: str,
        url: str,
        provider: str,
        country: str,
        subdivision: Optional[str] = None,
    ) -> None:
        self.name = name
        self.url = url
        self.provider = provider
        self.country = country
        self.subdivision = subdivision

    @classmethod
    def from_dict(cls, d: dict) -> "HttpResourceConfig":
        return cls(
            name=d["name"],
            url=d["url"],
            provider=d["provider"],
            country=d["country"],
            subdivision=d.get("subdivision"),
        )

    @property
    def filename(self) -> str:
        # WFS URLs have a meaningless path segment; derive filename from outputFormat.
        parsed = urlparse(self.url)
        fmt = parse_qs(parsed.query).get("outputFormat", [None])[0]
        if fmt:
            return f"source.{fmt.split('/')[-1].lower()}"
        path_name = parsed.path.split("/")[-1]
        return path_name if path_name else "source"

    def resolve_url(self) -> str:
        return self.url

    def resolve_version(self, context: dict) -> str:
        return context["ds"]

    def plan(self, run_date: datetime.date) -> CollectPlan:
        return self._download_plan(self.url, date_version(run_date))


class HttpHeadProbeConfig(HttpSource):
    """HEAD-probe resource: version from Last-Modified header."""

    url = None

    def __init__(
        self,
        name: str,
        provider: str,
        country: str,
        download_url: str,
        subdivision: Optional[str] = None,
    ) -> None:
        self.name = name
        self.provider = provider
        self.country = country
        self.download_url = download_url
        self.subdivision = subdivision

    @property
    def filename(self) -> str:
        path_name = urlparse(self.download_url).path.split("/")[-1]
        return path_name if path_name else "source"

    def _resolve(self, run_date: datetime.date | None = None) -> tuple[str, str]:
        """Return the URL and version; ``run_date`` (default today) is the fallback version."""
        resp = requests.head(self.download_url, timeout=30, allow_redirects=True)
        resp.raise_for_status()
        last_modified = resp.headers.get("Last-Modified", "")
        version = (
            parse_http_last_modified_version(last_modified)
            if last_modified
            else date_version(run_date or datetime.date.today())
        )
        return self.download_url, version

    def plan(self, run_date: datetime.date) -> CollectPlan:
        url, version = self._resolve(run_date)
        return self._download_plan(url, version)
