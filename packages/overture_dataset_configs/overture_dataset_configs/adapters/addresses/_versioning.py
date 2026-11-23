"""Version strings for sources that publish no explicit version."""

from datetime import timezone
from email.utils import parsedate_to_datetime


def parse_http_last_modified_version(last_modified: str) -> str:
    """Parse an HTTP Last-Modified header value into a nodash version string.

    Copy of ``overture_core.versioning.parse_http_last_modified_version``:
    overture-core depends on this package, so importing it here would make a cycle.

    >>> parse_http_last_modified_version("Sat, 01 Mar 2025 12:00:00 GMT")
    '20250301'
    """
    dt = parsedate_to_datetime(last_modified).astimezone(timezone.utc)
    return dt.strftime("%Y%m%d")
