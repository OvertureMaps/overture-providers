# overture-dataset-configs

[![PyPI](https://img.shields.io/pypi/v/overture-dataset-configs?color=4051CC&labelColor=001A39)](https://pypi.org/project/overture-dataset-configs/)
[![Test Python](https://github.com/OvertureMaps/overture-providers/actions/workflows/test_python.yml/badge.svg?branch=main)](https://github.com/OvertureMaps/overture-providers/actions/workflows/test_python.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-4051CC?labelColor=001A39)](https://github.com/OvertureMaps/overture-providers/blob/main/packages/overture_dataset_configs/pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-05A5AF?labelColor=001A39)](https://github.com/OvertureMaps/overture-providers/blob/main/packages/overture_dataset_configs/LICENSE)

Dataset configs for Overture providers, the per-theme license policy, and the classes that validate, load and render them.

```python
from overture_dataset_configs import load_config, provider_names
from overture_dataset_configs.dataset import Dataset
from overture_dataset_configs.license_policy import load_policy

provider_names()  # ["alltheplaces", "birdeye", ...]
load_config("linz")  # raw dict from overture_dataset_configs/datasets/linz.json

ds = Dataset.from_name("osm", "planet")  # packaged configs by default
ds.dataset_id, ds.license_type, ds.download_url

load_policy().allowed("places")  # {"CDLA-Permissive-2.0", ...}
```

| Module | Scope |
| --- | --- |
| `dataset` | `Dataset`: one provider/resource config, with its collection, ingestion and matching sections. |
| `schema` | Strict pydantic models for the config files; `python -m overture_dataset_configs.schema <files>` validates from the shell. |
| `license_policy` | `LicensePolicy`: validating and querying the per-theme license allowlist. |
| `attribution` | Flattening configs into license entries and rendering them as Markdown or plain text. |
| `spdx` | Fetching canonical SPDX license texts from a pinned `license-list-data` release. |
| `adapters.addresses` | Address source adapters: one class per fetch strategy, and loaders that pick one for each address dataset. |
| `cli` | The `overture-datasets` command. |

## Command line

Installing the package adds an `overture-datasets` command:

```bash
overture-datasets validate 'path/to/datasets/*.json' --policy path/to/license_policy.json
overture-datasets parse -d path/to/datasets acme:planet
overture-datasets license -d path/to/datasets acme globex -o ATTRIBUTION.md
overture-datasets policy check --policy path/to/license_policy.json --theme places -d path/to/datasets
```

Run `overture-datasets --help` for exit codes, and `overture-datasets <command> --help` for each command's flags.

## Address source adapters

```python
import datetime

from overture_dataset_configs.adapters.addresses import (
    fetch_all_oa_jobs,
    load_http_resources,
    load_oa_resources,
)
from overture_dataset_configs.dataset import DATASETS_DIR, Dataset

datasets = [d for p in DATASETS_DIR.glob("*.json") for d in Dataset.all_from_file(p)]
load_oa_resources(datasets)  # [OAResourceConfig, ...], one per open_addresses resource
fetch_all_oa_jobs("https://batch.openaddresses.io/api")  # {source: latest job id}

for source in load_http_resources(datasets):  # one HttpSource per HTTP resource
    plan = source.plan(datetime.date.today())
    plan.strategy, plan.url or plan.api_url, plan.version, plan.filename
```

Every HTTP adapter subclasses `HttpSource` and implements `plan`, which returns a `CollectPlan`: the strategy, the URL to download (or, for `http_signed_api`, the API that issues a short-lived signed URL at download time), the version and the destination filename.

Loaders choose a class by provider label, or by provider and resource label for providers that also publish non-address resources. `strategies.py` holds the fetch strategies several providers share; a provider whose source needs its own logic gets its own module, as `cuzk.py`, `gurs.py` and `us_dot_nad.py` do. A new address provider needs an entry in `loaders.py`, plus an `HttpSource` subclass in its own module when no shared strategy fits.

## Concepts

- **Provider**: an organization Overture takes data from, such as Land Information New Zealand.
- **Dataset** (a `resources` entry): one licensed collection of data from a provider, such as a single layer or file set. A provider can have many datasets, and each has its own license, coverage and refresh cadence.
- **License policy**: per theme, the license identifiers Overture accepts. Every dataset's license type should appear in it.

For how themes, attribution, and licensing work across Overture data, see the [Overture documentation](https://docs.overturemaps.org/): the [schema](https://docs.overturemaps.org/schema/) for themes, and the [attribution page](https://docs.overturemaps.org/attribution/) for the terms published with each release.

Each file in [`overture_dataset_configs/datasets`](https://github.com/OvertureMaps/overture-providers/tree/main/packages/overture_dataset_configs/overture_dataset_configs/datasets) describes one provider and its datasets. Files are named `<provider_label>.json` and looked up by file stem. The field reference is [`schema.py`](https://github.com/OvertureMaps/overture-providers/blob/main/packages/overture_dataset_configs/overture_dataset_configs/schema.py), which also rejects unknown keys.

## Contributing

1. Edit or add a file, then run `uv sync --extra dev` and `uv run pytest` from this directory. The tests validate every file against the schema, plus semantic checks (license ids and URLs, attribution, URL pairs), and render the attribution output (Markdown and text).
2. A new field needs a matching change to `schema.py` in the same PR.
3. Provider and resource labels feed dataset IDs and S3 paths, so don't rename them.
