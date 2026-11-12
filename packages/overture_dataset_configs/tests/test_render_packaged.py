"""Render every packaged config and check each required attribution survives."""

from pathlib import Path

import pytest
from overture_dataset_configs.attribution import RENDERERS, entries_from_file
from overture_dataset_configs.schema import validate_file

DATASETS = Path(__file__).parent.parent / "overture_dataset_configs" / "datasets"


@pytest.mark.parametrize("fmt", sorted(RENDERERS))
def test_render_includes_required_attributions(fmt):
    entries = [
        e
        for path in sorted(DATASETS.glob("*.json"))
        for e in entries_from_file(validate_file(path))
    ]
    rendered = RENDERERS[fmt](entries)
    required = {e["attribution"] for e in entries if e["requires_attribution"]}
    assert required
    assert not [a for a in required if a not in rendered]
