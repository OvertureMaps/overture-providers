"""Address source adapters: one class per fetch strategy, and loaders that pick
one for each address dataset config.
"""

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
