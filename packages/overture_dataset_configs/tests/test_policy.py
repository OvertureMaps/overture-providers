from pathlib import Path

from overture_core.dataset.license_policy import load_policy
from overture_dataset_configs import load_config, load_license_policy, provider_names

POLICY_FILE = (
    Path(__file__).parent.parent / "overture_dataset_configs" / "license_policy.json"
)


def test_policy_is_valid():
    policy = load_policy(POLICY_FILE)
    assert policy.root == load_license_policy()
    assert policy.themes


def test_every_config_license_is_in_some_theme_allowlist():
    policy = load_policy(POLICY_FILE)
    entries = [
        {
            "provider_label": name,
            "resource_label": r["label"],
            "license_type": r["collection"]["license"]["type"],
        }
        for name in provider_names()
        for r in load_config(name)["resources"]
        if r["collection"]["license"]
    ]
    assert entries
    assert policy.unlisted_licenses(entries) == {}
