from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)


def fetch_all_oa_jobs(api_base: str) -> dict[str, int]:
    """Return {source path: latest job ID} for all OA address resources."""
    resp = requests.get(f"{api_base}/data", params={"layer": "addresses"}, timeout=30)
    resp.raise_for_status()
    return {item["source"]: item["job"] for item in resp.json()}
