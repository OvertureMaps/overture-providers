from __future__ import annotations

from overture_dataset_configs.adapters.addresses.resource_configs import (
    CZResourceConfig,
    HttpHeadProbeConfig,
    HttpResourceConfig,
    OAResourceConfig,
    SIResourceConfig,
    SocrataResourceConfig,
)
from overture_dataset_configs.dataset import Dataset

# Provider → loader class. Adding a new addresses provider = one class + one
# entry here. Config JSON describes what/who/where; this registry owns how.
_OA_PROVIDER = "open_addresses"
_HTTP_LOADER_BY_PROVIDER: dict[str, type] = {
    "byggoastofnun": HttpResourceConfig,
    "nyc_dcp": HttpResourceConfig,
    "us_census_bureau": HttpResourceConfig,
    "pdok": HttpHeadProbeConfig,
    "stadfangaskra": HttpHeadProbeConfig,
    "cuzk": CZResourceConfig,
    "gurs": SIResourceConfig,
}

# (provider, resource) → loader class, checked first. For providers that also
# publish non-address resources: us_dot's HPMS is not a Socrata download.
_HTTP_LOADER_BY_RESOURCE: dict[tuple[str, str], type] = {
    ("us_dot", "nad"): SocrataResourceConfig,
}


def _http_loader_for(dataset: Dataset) -> type | None:
    return _HTTP_LOADER_BY_RESOURCE.get(
        (dataset.provider_label, dataset.resource_label)
    ) or _HTTP_LOADER_BY_PROVIDER.get(dataset.provider_label)


def load_oa_resources(datasets: list[Dataset]) -> list[OAResourceConfig]:
    """Build OA per-source configs from flattened OA datasets.

    Reads all OA-specific fields from `collection.extras` — each resource
    declares its own batch_api / batch_bucket / oa_batch_source, so no
    provider-level assumption is baked in.
    """
    results = []
    for dataset in datasets:
        if dataset.provider_label != _OA_PROVIDER:
            continue
        collection = dataset.collection
        extras = collection.get("extras", {})
        # US subdivision comes from coverage.areas[0].iso_3166_2 (e.g. "US-NY" → "NY").
        # Non-US resources leave subdivision_code as None — no downstream consumer today.
        areas = collection.get("coverage", {}).get("areas", [])
        iso_3166_2 = areas[0].get("iso_3166_2", "") if areas else ""
        subdivision_code = (
            iso_3166_2.split("-", 1)[1] if iso_3166_2.startswith("US-") else None
        )
        results.append(
            OAResourceConfig.from_dict(
                {
                    "source": extras["oa_batch_source"],
                    "batch_api": collection["api"]["url"],
                    "batch_bucket": extras["batch_bucket"],
                    "label": dataset.resource_label,
                    "subdivision_code": subdivision_code,
                    "dataset": dataset.resource_name,
                }
            )
        )
    return results


def load_http_resources(
    datasets: list[Dataset],
) -> list[
    HttpResourceConfig
    | HttpHeadProbeConfig
    | CZResourceConfig
    | SIResourceConfig
    | SocrataResourceConfig
]:
    """Build HTTP resource configs from datasets, dispatching by provider and resource label."""
    results = []
    for dataset in datasets:
        cls = _http_loader_for(dataset)
        if cls is None:
            continue
        collection = dataset.collection

        if cls in (HttpResourceConfig, HttpHeadProbeConfig):
            areas = dataset.coverage.get("areas", [])
            country = areas[0]["iso_3166_1"] if areas else None
            iso_3166_2 = areas[0].get("iso_3166_2") if areas else None
            subdivision = (
                iso_3166_2[0] if isinstance(iso_3166_2, list) and iso_3166_2 else None
            )
            common = {
                "name": dataset.resource_label,
                "provider": dataset.provider_label,
                "country": country,
                "subdivision": subdivision,
            }
            if cls is HttpResourceConfig:
                results.append(HttpResourceConfig(url=dataset.download_url, **common))
            else:
                results.append(
                    HttpHeadProbeConfig(download_url=dataset.download_url, **common)
                )
        else:
            results.append(cls.from_dict(collection))
    return results
