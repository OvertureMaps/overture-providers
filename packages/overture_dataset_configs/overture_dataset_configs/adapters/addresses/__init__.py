"""Address source adapters: one class per fetch strategy, and loaders that pick
one for each address dataset config.

Needs the ``addresses`` extra: ``pip install 'overture-dataset-configs[addresses]'``.
"""

try:
    import requests  # noqa: F401
except ImportError as e:
    raise ImportError(
        "overture_dataset_configs.adapters.addresses needs the 'addresses' extra: "
        "pip install 'overture-dataset-configs[addresses]'"
    ) from e

from overture_dataset_configs.adapters.addresses.collect import fetch_all_oa_jobs
from overture_dataset_configs.adapters.addresses.loaders import (
    load_http_resources,
    load_oa_resources,
)
from overture_dataset_configs.adapters.addresses.resource_configs import (
    CZResourceConfig,
    HttpHeadProbeConfig,
    HttpResourceConfig,
    OAResourceConfig,
    SIResourceConfig,
    SocrataResourceConfig,
)

__all__ = [
    "CZResourceConfig",
    "HttpHeadProbeConfig",
    "HttpResourceConfig",
    "OAResourceConfig",
    "SIResourceConfig",
    "SocrataResourceConfig",
    "fetch_all_oa_jobs",
    "load_http_resources",
    "load_oa_resources",
]
