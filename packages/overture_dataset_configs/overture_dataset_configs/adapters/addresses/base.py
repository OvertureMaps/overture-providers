"""The interface every HTTP address source adapter implements."""

from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class CollectPlan:
    """What a collect job fetches for one resource, and where it lands.

    ``http_download`` fetches ``url``. ``http_signed_api`` asks ``api_url``
    for a short-lived signed URL inside the collect job, so it can't expire
    between planning and download.
    """

    strategy: Literal["http_download", "http_signed_api"]
    version: str
    filename: str
    url: Optional[str] = None
    api_url: Optional[str] = None


class HttpSource(ABC):
    """An address resource collected over HTTP.

    Subclasses set ``provider`` and ``name`` (the dataset's provider and
    resource labels) and implement ``plan``.
    """

    provider: str
    name: str

    @abstractmethod
    def plan(self, run_date: datetime.date) -> CollectPlan:
        """Resolve the URL and version to collect for a run on ``run_date``."""

    def _download_plan(self, url: str, version: str) -> CollectPlan:
        # ZIP archives land as source.zip and are extracted at ingest time.
        filename = (
            "source.zip"
            if url.lower().endswith(".zip")
            else (getattr(self, "filename", None) or "source")
        )
        return CollectPlan("http_download", version, filename, url=url)
