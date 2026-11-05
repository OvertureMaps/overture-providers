![overture-providers: provider metadata for Overture, as Python packages](assets/hero.svg)

[![Test Python](https://github.com/OvertureMaps/overture-providers/actions/workflows/test_python.yml/badge.svg?branch=main)](https://github.com/OvertureMaps/overture-providers/actions/workflows/test_python.yml)
[![Lint](https://github.com/OvertureMaps/overture-providers/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/OvertureMaps/overture-providers/actions/workflows/lint.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-4051CC?labelColor=001A39)](../.python-version)
[![uv](https://img.shields.io/badge/managed%20with-uv-0EC1BD?labelColor=001A39)](https://docs.astral.sh/uv/)
[![Ruff](https://img.shields.io/badge/lint-ruff-0EC1BD?labelColor=001A39)](https://docs.astral.sh/ruff/)
[![License: MIT](https://img.shields.io/badge/license-MIT-05A5AF?labelColor=001A39)](../LICENSE)

Metadata about the data providers behind Overture releases: which datasets feed each theme, and the license and attribution details for each provider. Each package under [packages/](../packages) is versioned and published to PyPI on its own.

## Packages

| Package | Install | What it holds |
| --- | --- | --- |
| [overture_sources](../packages/overture_sources) | `pip install overture-sources` | Deprecated in favor of overture_dataset_configs. Source registry: the datasets that feed each theme, with license, coverage and refresh details. |
| [overture_dataset_configs](../packages/overture_dataset_configs) | `pip install overture-dataset-configs` | Per-provider dataset configs and the per-theme license policy, with classes to validate, load and render attribution from them. |

Each package's tests validate its JSON files in CI.

## Releases

Merging to `main` releases any package whose changes warrant a version bump. The PR title's [Conventional Commits](https://www.conventionalcommits.org/) type sets the bump (`fix:` patch, `feat:` minor, `!` major), and the release is tagged `<package_dir>-v<version>`. See [PACKAGE_VERSIONING.md](PACKAGE_VERSIONING.md) for the flow and the one-time PyPI setup a new package needs.

## Contributing

See [CONTRIBUTING.md](../.github/CONTRIBUTING.md) for adding a package and running tests and lint locally.
