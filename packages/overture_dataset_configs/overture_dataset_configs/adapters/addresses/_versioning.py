"""Version strings for sources that publish no explicit version.

Every address adapter labels versions ``YYYYMMDD``. overture-core orders
partition values by their digit runs as integers, so a ``YYYYMMDD`` version
sorts after any older ``YYYY-MM-DD`` one.
"""

import datetime
from datetime import timezone
from email.utils import parsedate_to_datetime


def date_version(d: datetime.date) -> str:
    """Format a date as a version string.

    >>> date_version(datetime.date(2026, 5, 15))
    '20260515'
    """
    return d.strftime("%Y%m%d")


def parse_http_last_modified_version(last_modified: str) -> str:
    """Parse an HTTP Last-Modified header value into a nodash version string.

    Copy of ``overture_core.versioning.parse_http_last_modified_version``:
    overture-core depends on this package, so importing it here would make a cycle.

    >>> parse_http_last_modified_version("Sat, 01 Mar 2025 12:00:00 GMT")
    '20250301'
    """
    dt = parsedate_to_datetime(last_modified).astimezone(timezone.utc)
    return dt.strftime("%Y%m%d")
