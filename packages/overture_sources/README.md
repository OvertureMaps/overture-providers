# overture-sources

[![PyPI](https://img.shields.io/pypi/v/overture-sources?color=4051CC&labelColor=001A39)](https://pypi.org/project/overture-sources/)
[![Test Python](https://github.com/OvertureMaps/overture-providers/actions/workflows/test_python.yml/badge.svg?branch=main)](https://github.com/OvertureMaps/overture-providers/actions/workflows/test_python.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-4051CC?labelColor=001A39)](https://github.com/OvertureMaps/overture-providers/blob/main/packages/overture_sources/pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-05A5AF?labelColor=001A39)](https://github.com/OvertureMaps/overture-providers/blob/main/packages/overture_sources/LICENSE)

Overture source registry: the JSON files describing the datasets that feed each theme.

> [!WARNING]
> Deprecated in favor of [overture-dataset-configs](https://pypi.org/project/overture-dataset-configs/), which holds the same per-dataset license, attribution and coverage details. This package is kept for existing consumers of the per-theme files; new code should use the dataset configs.

```python
from overture_sources import load_sources, theme_names

theme_names()  # ["addresses", "base", ...]
load_sources("places")  # parsed overture_sources/places.json
```

## Concepts

- **Theme**: a top-level Overture data category, such as places or buildings. There is one file per theme, plus `property_descriptions`. See the [Overture schema documentation](https://docs.overturemaps.org/schema/) for what each theme contains.
- **Source**: an organization whose data contributes to a theme.
- **Dataset**: one specific collection of data from a source. Its `dataset_name` is a readable label, unique together with `source_name`. For most themes it is the value that appears as `dataset` in a feature's `sources` property in Overture data. Addresses are the exception: OpenAddresses datasets are named `OpenAddresses/<country>/<subdivision>/<name>` (subdivision only when the coverage names one, codes from ISO 3166), while the `dataset` value in the data is the OpenAddresses path, such as `us/ca/santa_clara`.

Each theme file has a `datasets` list, with one entry per source and dataset pair, plus a `license_priority` mapping of license identifiers to a priority rank. An entry records the dataset's license, attribution, coverage, refresh cadence and the date it was first used in the theme. `property_descriptions.json` documents every field.

For the attribution and license terms as published with each release, see the [Overture attribution page](https://docs.overturemaps.org/attribution/).
