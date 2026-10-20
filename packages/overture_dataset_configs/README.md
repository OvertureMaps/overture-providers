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

## Config files

Each file in [`overture_dataset_configs/datasets`](overture_dataset_configs/datasets) describes one provider and the resources (datasets) taken from it. Files are named `<provider_label>.json` and looked up by file stem. The field reference is the [overture-core dataset schema](https://github.com/OvertureMaps/overture-core/blob/main/packages/overture_core/overture_core/dataset/README.md), which also rejects unknown keys.

## Contributing

1. Edit or add a file, then run `uv sync --extra dev` and `uv run pytest` from this directory. The tests validate every file against the overture-core schema, plus semantic checks (license ids, attribution, URL pairs).
2. A new field goes in the overture-core schema first.
3. Provider and resource labels feed dataset IDs and S3 paths, so don't rename them.
