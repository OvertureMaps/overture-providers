"""Address source adapters and the loaders that pick one for each address dataset.

``base`` defines ``HttpSource``, the interface every HTTP adapter implements, and
the ``CollectPlan`` its ``plan`` returns. ``strategies`` holds fetch strategies
shared by several providers; ``cuzk``, ``gurs`` and ``us_dot_nad`` hold adapters
specific to one provider.
"""

from overture_dataset_configs.adapters.addresses.base import CollectPlan, HttpSource
from overture_dataset_configs.adapters.addresses.collect import fetch_all_oa_jobs
from overture_dataset_configs.adapters.addresses.loaders import (
    load_http_resources,
    load_oa_resources,
)
from overture_dataset_configs.adapters.addresses.cuzk import CZResourceConfig
from overture_dataset_configs.adapters.addresses.gurs import SIResourceConfig
from overture_dataset_configs.adapters.addresses.strategies import (
    HttpHeadProbeConfig,
    HttpResourceConfig,
    OAResourceConfig,
)
from overture_dataset_configs.adapters.addresses.us_dot_nad import SocrataResourceConfig

__all__ = [
    "CollectPlan",
    "HttpSource",
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
