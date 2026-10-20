# overture-dataset-configs

Public dataset license/policy configs for Overture Maps providers.

```python
from overture_dataset_configs import load_config, load_license_policy, provider_names

provider_names()  # ["alltheplaces", "birdeye", ...]
load_config("linz")  # parsed JSON for overture_dataset_configs/datasets/linz.json
load_license_policy()  # {theme: [allowed license ids]} from overture_dataset_configs/license_policy.json
```

## Dataset config files

Each JSON file in [`overture_dataset_configs/datasets`](overture_dataset_configs/datasets)
describes one **provider** and the **resources** (datasets) we take from that
provider. Files are named `<provider_label>.json` (e.g. `open_addresses.json`)
and are looked up by file stem via `load_config`.

Every file is validated against the pydantic schema in
[`overture_core.dataset.schema`](https://github.com/OvertureMaps/overture-core/blob/main/packages/overture_core/overture_core/dataset/schema.py).
Validation runs in this package's tests (`overture-core` is a dev-only
dependency; the package itself has none). Unknown keys are **rejected** — if
you need a new field, add it to the schema in `overture-core` and document it
here.

## Top-level structure

```json
{
  "provider": { ... },
  "resources": [ { ... }, ... ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `provider` | object | yes | The organization the data comes from. One per file. |
| `resources` | array of objects | yes, ≥ 1 entry | The datasets taken from this provider. Resource `label`s must be unique within the file. |

## `provider`

| Field | Type | Required | Description |
|---|---|---|---|
| `label` | string | yes | Stable machine identifier in snake_case (`^[a-z0-9_]+$`), e.g. `open_addresses`. Used as the first half of the `dataset_id` (`<provider_label>_<resource_label>`) and in S3 partition paths (`provider=<label>`). Must be unique across all files and must match the file stem (`open_addresses.json` → `open_addresses`). |
| `name` | string | yes, non-empty | Human-readable display name, e.g. `OpenAddresses`. Used in attribution artifacts. |
| `url` | object | yes | Provider homepage as a [URL pair](#url-pairs). |

## `resources[]`

| Field | Type | Required | Description |
|---|---|---|---|
| `label` | string | yes | Stable machine identifier in snake_case (`^[a-z0-9_]+$`), unique within the file, e.g. `at_countrywide`. Second half of the `dataset_id`; used in S3 partition paths (`resource=<label>`). |
| `name` | string | yes, non-empty | Human-readable resource name, e.g. `Esri Community Maps` or `open_addresses/at/countrywide`. Used in attribution artifacts. |
| `collection` | object | yes | Describes the data: where it lives, how it's licensed, what it covers, and how often it refreshes. See below. |
| `ingestion` | object | yes | Free-form ingestion pipeline configuration, read by the ingest DAG and forwarded to the ingest job as parameters. `{}` for resources with no ingestion config of their own. See [below](#resourcesingestion). |
| `matching` | object | yes | Free-form entity-matching pipeline configuration. Usually `{}`. |

## `resources[].collection`

| Field | Type | Required | Description |
|---|---|---|---|
| `data_location` | object | yes | Landing/metadata page describing the data, as a [URL pair](#url-pairs). May be empty strings when the data has no public landing page. |
| `data_download` | object | no | Direct download location. See [`data_download`](#resourcescollectiondata_download) below. Omitted for providers fetched by other means (e.g. OpenAddresses batch bucket). |
| `license` | object | yes | License and attribution terms. See below. |
| `coverage` | object | yes | Geographic coverage. See below. |
| `refresh_schedule` | object | no | How and when the source publishes updates. See below. |
| `known_issues` | string | no | Free-text description of known data quality problems. |
| `notes` | string | yes (may be `""`) | Free-text notes: provenance, distribution details, links to upstream configs, etc. |
| `api` | object | no | API used to discover or fetch the data. Single key `url` (non-empty string), e.g. the OpenAddresses batch API or a Socrata metadata endpoint. |
| `extras` | object of string→string | no | Free-form provider-specific settings consumed by that provider's loader. E.g. OpenAddresses uses `batch_bucket` and `oa_batch_source`. |

## `resources[].collection.data_download`

Where and how the collect DAGs fetch the raw data. `Dataset.download_url`
returns `url + endpoint`.

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | string | yes | Transport: `http`, `s3`, or `hf` (Hugging Face). Must match the `url` scheme. |
| `url` | non-empty string | yes | Base download location: HTTP(S) URL, `s3://` URI, or `hf://` URI. Some loaders (e.g. `cuzk`) treat it as a URL template. |
| `endpoint` | string | no | Sub-path appended to `url`, e.g. a geoBoundaries API path like `AGO/ADM2/`. Defaults to `""`. |

## `resources[].collection.license`

| Field | Type | Required | Description |
|---|---|---|---|
| `url` | object | yes | Where the license terms are published, as a [URL pair](#url-pairs). |
| `type` | string | yes | License identifier. Use an SPDX identifier when one exists (`CC-BY-4.0`, `ODbL-1.0`, `CDLA-Permissive-2.0`, ...); otherwise use the SPDX-compliant `LicenseRef-*` string. |
| `requires_attribution` | boolean | yes | Whether the license requires attribution. When `true`, `attribution` must be non-empty. |
| `text` | string | yes (may be `""`) | Relevant excerpt of the license terms. |
| `attribution` | string | yes (may be `""`) | Exact attribution string to display, e.g. `© Österreichisches Adressregister, data of the record date 01.4.2025`. Surfaced in the released `license.json` / `attribution.mdx` artifacts. |

## `resources[].collection.coverage`

| Field | Type | Required | Description |
|---|---|---|---|
| `areas` | array of objects | yes, ≥ 1 entry | Regions the data covers. |
| `areas[].iso_3166_1` | string | yes | ISO 3166-1 alpha-2 country code (`US`, `AT`, ...) or the literal `GLOBAL` for worldwide coverage. |
| `areas[].iso_3166_2` | string | no | ISO 3166-2 subdivision code (`US-NY`, `JP-13`, ...) when coverage is sub-national. |
| `description` | string | yes (may be `""`) | Human-readable coverage summary, e.g. `Global` or `New York City`. |

## `resources[].collection.refresh_schedule`

| Field | Type | Required | Description |
|---|---|---|---|
| `frequency` | string | yes | Upstream publish cadence. One of `Daily`, `Weekly`, `Monthly`, `Semi-annually`, `Annually`, `Infrequent`, `None` (source is static), or `""` (unknown). |
| `source` | string | no | Who collects the data on that cadence, e.g. `tf-data-platform` (our collect DAGs) or `OpenAddresses`. |
| `type` | string | no | `continuous` (collected automatically on a schedule) or `manual` (collected by hand when the source updates). |
| `month` | array of integers (1–12) | no | Months in which updates are expected, for non-continuous sources. `[]` when not applicable. |

## `resources[].ingestion`

Free-form: the schema types this block `dict[str, Any]`, so keys here are not
validated the way the rest of the file is. Each key is read by the theme's
ingest DAG and passed to the ingest job as a parameter of the same name, so a
policy change here ships with a DAG deploy rather than a package release.

Keys in use today:

| Key | Read by | Description |
|---|---|---|
| `country_category_filters` | `theme_places_ingest_dag` → `PlacesFeedIngestJob` (BrightQuery only) | Which countries the feed is ingested for, and which taxonomy categories are dropped per country. `country_policy` is `"allowlist"` (ingest only the countries listed under `countries`) or `"all"` (ingest every country; an entry then only excludes categories for that one country, and a country with no entry falls back to `default.excluded_categories`). Each country entry needs `excluded_categories` (taxonomy category names, validated against `overture_taxonomy.json` by the `overture_places` tests) and should carry a `reason`. |

```json
"ingestion": {
  "country_category_filters": {
    "country_policy": "allowlist",
    "default": { "excluded_categories": [] },
    "countries": {
      "DE": {
        "excluded_categories": ["amusement_park", "hospital"],
        "reason": "BrightQuery coverage for these categories in DE is unreliable"
      }
    }
  }
}
```

## URL pairs

Several fields hold a pair of URLs:

| Field | Type | Required | Description |
|---|---|---|---|
| `primary` | string | yes (may be `""`) | The live URL. |
| `archive` | string | yes (may be `""`) | A web.archive.org snapshot of the live URL, so license/coverage claims stay verifiable if the source changes. |

## Adding or changing a file

1. Follow the structure above; run the validator locally:
   `uv run pytest` from this directory (after `uv sync --extra dev`).
2. New field? Add it to the schema in `overture-core` and to this README.
3. Provider/resource `label`s are load-bearing (dataset IDs, S3 paths) — never
   rename them casually.
