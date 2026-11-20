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

For a command line, overture-core's `overture-datasets` CLI validates and renders these configs.

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
