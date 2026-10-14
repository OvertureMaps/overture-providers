# overture-providers

A monorepo of independently versioned, independently published Python packages for Overture Maps data providers. Each directory under [`packages/`](packages) with a `pyproject.toml` and a `tests/` directory is one package.

## Packages

| Package | Description |
| --- | --- |
| [`overture_sources`](packages/overture_sources) | Source registry (port of tf-data-platform `sources`). |
| [`overture_dataset_configs`](packages/overture_dataset_configs) | Public dataset license/policy configs. |

## Contributing

See [`CONTRIBUTING.md`](.github/CONTRIBUTING.md) for how to add a package and run tests/lint locally.
