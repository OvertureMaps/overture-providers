# overture-sources

[![PyPI](https://img.shields.io/pypi/v/overture-sources)](https://pypi.org/project/overture-sources/)
[![License](https://img.shields.io/pypi/l/overture-sources)](LICENSE)

Overture source registry: the JSON files describing the datasets that feed each theme.

```python
from overture_sources import load_sources, theme_names

theme_names()  # ["addresses", "base", ...]
load_sources("places")  # parsed overture_sources/places.json
```

## Concepts

- **Theme**: a top-level Overture data category, such as places or buildings. There is one file per theme, plus `property_descriptions`.
- **Source**: an organization whose data contributes to a theme.
- **Dataset**: one specific collection of data from a source. Its `dataset_name` is the value that appears as `dataset` in a feature's `sources` property in Overture data.

Each theme file has a `datasets` list, with one entry per source and dataset pair, plus a `license_priority` mapping of license identifiers to a priority rank. An entry records the dataset's license, attribution, coverage, refresh cadence and the date it was first used in the theme. `property_descriptions.json` documents every field.

To see which datasets are taken from a provider and under which license policy, see [overture-dataset-configs](https://pypi.org/project/overture-dataset-configs/).
