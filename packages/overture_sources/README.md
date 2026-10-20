# overture-sources

Overture Maps source registry: the JSON files describing the datasets that feed each theme.

```python
from overture_sources import load_sources, theme_names

theme_names()  # ["addresses", "base", ...]
load_sources("places")  # parsed overture_sources/places.json
```
