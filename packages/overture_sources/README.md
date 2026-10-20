# overture-sources

[![PyPI](https://img.shields.io/pypi/v/overture-sources)](https://pypi.org/project/overture-sources/)
[![License](https://img.shields.io/pypi/l/overture-sources)](LICENSE)

Overture source registry: the JSON files describing the datasets that feed each theme.

```python
from overture_sources import load_sources, theme_names

theme_names()  # ["addresses", "base", ...]
load_sources("places")  # parsed overture_sources/places.json
```
