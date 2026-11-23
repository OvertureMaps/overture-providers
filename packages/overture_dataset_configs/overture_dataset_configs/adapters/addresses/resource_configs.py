from __future__ import annotations

import datetime
from datetime import timezone
from email.utils import parsedate_to_datetime
from typing import Optional
from urllib.parse import urlparse, parse_qs

import requests


def _parse_http_last_modified_version(last_modified: str) -> str:
    """Parse an HTTP Last-Modified header value into a nodash version string.

    Copy of ``overture_core.versioning.parse_http_last_modified_version``:
    overture-core depends on this package, so importing it here would make a cycle.

    >>> _parse_http_last_modified_version("Sat, 01 Mar 2025 12:00:00 GMT")
    '20250301'
    """
    dt = parsedate_to_datetime(last_modified).astimezone(timezone.utc)
    return dt.strftime("%Y%m%d")


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


class HttpResourceConfig:
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


_SI_API_URL = "https://ipi.eprostor.gov.si/jgp-service-api/display-views/groups/121/composite-products/141/file?filterParam=DRZAVA&filterValue=1"


class SIResourceConfig:
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


_CZ_URL_TEMPLATE = "https://vdp.cuzk.gov.cz/vymenny_format/csv/{date}_OB_ADR_csv.zip"


class CZResourceConfig:
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
                    _parse_http_last_modified_version(last_modified)
                    if last_modified
                    else candidate.strftime("%Y%m%d")
                )
                return url, version
            candidate = candidate.replace(day=1) - datetime.timedelta(days=1)
        raise RuntimeError("ČÚZK: no published file found in the last 3 months")

    def resolve_url(self) -> str:
        url, _ = self._resolve()
        return url

    def resolve_version(self, _context: dict) -> str:
        _, version = self._resolve()
        return version


_NAD_SOCRATA_API = "https://data.transportation.gov/api/views/fc2s-wawr.json"


class SocrataResourceConfig:
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
            socrata_api=d.get("api", {}).get("url", _NAD_SOCRATA_API),
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


class HttpHeadProbeConfig:
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

    def _resolve(self) -> tuple[str, str]:
        resp = requests.head(self.download_url, timeout=30, allow_redirects=True)
        resp.raise_for_status()
        last_modified = resp.headers.get("Last-Modified", "")
        version = (
            _parse_http_last_modified_version(last_modified)
            if last_modified
            else datetime.date.today().strftime("%Y%m%d")
        )
        return self.download_url, version
