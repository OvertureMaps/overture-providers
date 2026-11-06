"""Pydantic schema for dataset config files.

Unknown keys are rejected, so adding a new field to a config file requires
extending the models here in the same change.

Functions take explicit paths, so the same schema validates the packaged
configs and any other copy. See ``overture_dataset_configs.dataset`` for the
permissive runtime loader over that same JSON shape.

Run as a script to validate specific files:

    python -m overture_dataset_configs.schema path/to/provider.json ...
"""

from __future__ import annotations

import json
import re
import sys
from functools import cache
from pathlib import Path
from typing import Annotated, Any, Literal, get_args

import botocore
import botocore.session
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator


@cache
def get_s3_regions() -> frozenset[str]:
    """S3 regions across all partitions known to the installed botocore.

    The list is bundled with botocore, so regions launched after the installed
    release are missing.
    """
    session = botocore.session.get_session()
    return frozenset(
        region
        for partition in session.get_available_partitions()
        for region in session.get_available_regions("s3", partition_name=partition)
    )


LABEL_PATTERN = r"^[a-z0-9_]+$"
ISO_3166_1_PATTERN = r"^([A-Z]{2}|GLOBAL)$"
ISO_3166_2_PATTERN = r"^[A-Z]{2}-[A-Z0-9]{1,3}$"

Label = Annotated[str, Field(pattern=LABEL_PATTERN)]
NonEmptyStr = Annotated[str, Field(min_length=1)]
Month = Annotated[int, Field(ge=1, le=12)]

Theme = Literal[
    "addresses", "base", "buildings", "divisions", "places", "transportation"
]
THEMES: tuple[str, ...] = get_args(Theme)


def _no_duplicates(kind: str):
    def check(values: list[str]) -> list[str]:
        dupes = sorted({v for v in values if values.count(v) > 1})
        if dupes:
            raise ValueError(f"duplicate {kind}: {dupes}")
        return values

    return check


# Overture themes a dataset feeds. Set on the file to cover every resource;
# a resource's own value replaces the file-level one for that resource.
Themes = Annotated[
    list[Theme], Field(min_length=1), AfterValidator(_no_duplicates("themes"))
]

# How often the source publishes new data. "Biweekly" means every two weeks.
Frequency = Literal[
    "",
    "None",
    "Daily",
    "Weekly",
    "Biweekly",
    "Monthly",
    "Semi-annually",
    "Annually",
    "Infrequent",
]
FREQUENCIES: tuple[str, ...] = get_args(Frequency)

# How raw data reaches Overture. See `Delivery`.
DeliveryMethod = Literal["api", "bucket", "file_download"]
DeliveryDirection = Literal["pull", "push"]
DeliveryAuth = Literal["none", "iam", "api_key"]
DeliveryTrigger = Literal["scheduled", "manual"]
DataFormat = Literal[
    "csv",
    "geojson",
    "gpkg",
    "json",
    "osm_pbf",
    "parquet",
    "shapefile",
    "tsv",
    "xlsx",
]
DELIVERY_METHODS: tuple[str, ...] = get_args(DeliveryMethod)
DELIVERY_DIRECTIONS: tuple[str, ...] = get_args(DeliveryDirection)
DELIVERY_AUTHS: tuple[str, ...] = get_args(DeliveryAuth)
DELIVERY_TRIGGERS: tuple[str, ...] = get_args(DeliveryTrigger)
DATA_FORMATS: tuple[str, ...] = get_args(DataFormat)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class UrlPair(_StrictModel):
    """A live URL plus its web.archive.org snapshot. Either may be empty."""

    primary: str
    archive: str


class Provider(_StrictModel):
    label: Label
    name: NonEmptyStr
    url: UrlPair


class License(_StrictModel):
    url: UrlPair
    type: str | None = None
    requires_attribution: bool
    text: str
    attribution: str

    @model_validator(mode="after")
    def _attribution_required(self) -> License:
        if self.requires_attribution and not self.attribution:
            raise ValueError(
                "attribution must be non-empty when requires_attribution is true"
            )
        return self


class CoverageArea(_StrictModel):
    iso_3166_1: Annotated[str, Field(pattern=ISO_3166_1_PATTERN)]
    iso_3166_2: Annotated[str, Field(pattern=ISO_3166_2_PATTERN)] | None = None


class Coverage(_StrictModel):
    areas: Annotated[list[CoverageArea], Field(min_length=1)]
    description: str


class RefreshSchedule(_StrictModel):
    frequency: Frequency
    source: str | None = None
    type: Literal["continuous", "manual"] | None = None
    month: list[Month] | None = None


class Api(_StrictModel):
    url: NonEmptyStr


class DataDownload(_StrictModel):
    """Where and how to fetch the raw resource.

    `type` names the transport, `url` is the base location, and `endpoint`
    is an optional sub-path appended to it (see `Dataset.download_url`).
    `region` is the AWS region of the bucket and is only valid for `s3`.
    """

    type: Literal["http", "s3", "hf"]
    url: NonEmptyStr
    endpoint: str = ""
    region: str | None = None

    @model_validator(mode="after")
    def _region_only_for_s3(self) -> DataDownload:
        if self.region is None:
            return self
        if self.type != "s3":
            raise ValueError(f"region is only valid for type 's3', got '{self.type}'")
        if self.region not in get_s3_regions():
            raise ValueError(
                f"unknown S3 region '{self.region}' (botocore {botocore.__version__}); "
                "if this is a new AWS region, upgrade botocore"
            )
        return self

    @model_validator(mode="after")
    def _url_scheme_matches_type(self) -> DataDownload:
        prefixes = {
            "http": ("http://", "https://"),
            "s3": ("s3://",),
            "hf": ("hf://",),
        }[self.type]
        if not self.url.startswith(prefixes):
            raise ValueError(
                f"url scheme does not match type '{self.type}': {self.url}"
            )
        return self


class Delivery(_StrictModel):
    """How raw data reaches Overture: the omf_staff#52 ingest catalog fields.

    Purely descriptive; nothing in the pipeline reads it. Every field is
    optional so unknown values stay unset rather than guessed, but an empty
    object is rejected. The endpoint lives in `data_download` / `api`, and
    the source's update cadence in `refresh_schedule.frequency`.

    - `method`: `api` (we call a service to query or export the data, or to
      get a short-lived download link), `bucket` (an S3 object copy or read),
      or `file_download` (a static file over HTTP or from Hugging Face).
    - `direction`: `pull` (we fetch from the provider) or `push` (the
      provider drops data into our bucket).
    - `auth`: what our side needs to get the data: `none`, `iam` (AWS
      credentials, e.g. a cross-account bucket policy or requester-pays),
      or `api_key` (an API key or access token).
    - `trigger`: what starts collecting a new version: `scheduled` (an
      Airflow schedule fetches or checks for new data) or `manual` (a
      person must run something or download or upload files).
    - `formats`: file formats of the raw data as delivered, ignoring
      compression and ZIP archives.
    """

    method: DeliveryMethod | None = None
    direction: DeliveryDirection | None = None
    auth: DeliveryAuth | None = None
    trigger: DeliveryTrigger | None = None
    formats: (
        Annotated[
            list[DataFormat],
            Field(min_length=1),
            AfterValidator(_no_duplicates("formats")),
        ]
        | None
    ) = None

    @model_validator(mode="after")
    def _not_empty(self) -> Delivery:
        if all(getattr(self, name) is None for name in type(self).model_fields):
            raise ValueError("delivery must set at least one field")
        return self


class Collection(_StrictModel):
    data_location: UrlPair
    data_download: DataDownload | None = None
    delivery: Delivery | None = None
    license: License | None
    coverage: Coverage
    refresh_schedule: RefreshSchedule | None = None
    known_issues: str | None = None
    notes: str
    api: Api | None = None
    extras: dict[str, str] | None = None


class Resource(_StrictModel):
    label: Label
    name: NonEmptyStr
    themes: Themes | None = None
    collection: Collection
    # Free-form pipeline configs; intentionally unvalidated.
    ingestion: dict[str, Any]
    matching: dict[str, Any]


class DatasetFile(_StrictModel):
    provider: Provider
    themes: Themes | None = None
    # Default for resources whose `collection` sets no `delivery`; a
    # resource's own value replaces it whole, without merging fields.
    delivery: Delivery | None = None
    resources: Annotated[list[Resource], Field(min_length=1)]

    @model_validator(mode="after")
    def _unique_resource_labels(self) -> DatasetFile:
        labels = [r.label for r in self.resources]
        dupes = sorted({label for label in labels if labels.count(label) > 1})
        if dupes:
            raise ValueError(f"duplicate resource labels: {dupes}")
        return self


def validate_file(path: str | Path) -> DatasetFile:
    """Validate one dataset config file; raises ValueError on any problem."""
    path = Path(path)
    if not re.fullmatch(LABEL_PATTERN, path.stem):
        raise ValueError(f"file name must be snake_case: {path.name}")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except OSError as e:
        raise ValueError(f"could not read {path}: {e}") from e
    parsed = DatasetFile.model_validate(data)
    if parsed.provider.label != path.stem:
        raise ValueError(
            f"provider label '{parsed.provider.label}' must match file stem '{path.stem}'"
        )
    return parsed


def validate_all(paths: list[Path]) -> list[tuple[Path, ValueError]]:
    """Validate the given files.

    Returns a list of (path, error) tuples; empty means everything passed.
    Also checks that provider labels are unique across the given files.
    """
    errors: list[tuple[Path, ValueError]] = []
    provider_labels: dict[str, Path] = {}
    for path in paths:
        try:
            parsed = validate_file(path)
        except ValueError as exc:  # includes json.JSONDecodeError, ValidationError
            errors.append((path, exc))
            continue
        label = parsed.provider.label
        if label in provider_labels:
            errors.append(
                (
                    path,
                    ValueError(
                        f"provider label '{label}' already used by {provider_labels[label].name}"
                    ),
                )
            )
        else:
            provider_labels[label] = path
    return errors


def main(argv: list[str] | None = None) -> int:
    """Validate the dataset config files passed as arguments, e.g.:

    python -m overture_dataset_configs.schema path/to/datasets/*.json
    """
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print(
            "usage: python -m overture_dataset_configs.schema <path/to/provider.json> ...",
            file=sys.stderr,
        )
        return 2
    paths = [Path(a) for a in args]
    errors = validate_all(paths)
    for path, exc in errors:
        print(f"FAIL {path}:\n{exc}\n", file=sys.stderr)
    print(f"{len(paths) - len(errors)}/{len(paths)} dataset config files valid")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
