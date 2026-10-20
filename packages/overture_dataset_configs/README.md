# overture-dataset-configs

[![PyPI](https://img.shields.io/pypi/v/overture-dataset-configs)](https://pypi.org/project/overture-dataset-configs/)
[![License](https://img.shields.io/pypi/l/overture-dataset-configs)](LICENSE)

Public dataset license/policy configs for Overture providers.

```python
from overture_dataset_configs import load_config, load_license_policy, provider_names

provider_names()  # ["alltheplaces", "birdeye", ...]
load_config("linz")  # parsed overture_dataset_configs/datasets/linz.json
load_license_policy()  # {theme: [allowed license ids]}
```

This package only ships the data. For typed access (`Dataset`), license-policy checks, attribution generation, and the `overture-datasets` CLI, use [overture-core](https://pypi.org/project/overture-core/).

## Concepts

- **Provider**: an organization Overture takes data from, such as Land Information New Zealand.
- **Dataset** (a `resources` entry): one licensed collection of data from a provider, such as a single layer or file set. A provider can have many datasets, and each has its own license, coverage and refresh cadence.
- **License policy**: per theme, the license identifiers Overture accepts. Every dataset's license type should appear in it.

Each file in [`overture_dataset_configs/datasets`](overture_dataset_configs/datasets) describes one provider and its datasets. Files are named `<provider_label>.json` and looked up by file stem. The field reference is the [overture-core dataset schema](https://github.com/OvertureMaps/overture-core/blob/main/packages/overture_core/overture_core/dataset/README.md), which also rejects unknown keys.

The [source registry](https://pypi.org/project/overture-sources/) is the published, per-theme view of these inputs.

## Contributing

1. Edit or add a file, then run `uv sync --extra dev` and `uv run pytest` from this directory. The tests validate every file against the overture-core schema, plus semantic checks (license ids, attribution, URL pairs).
2. A new field goes in the overture-core schema first.
3. Provider and resource labels feed dataset IDs and S3 paths, so don't rename them.
