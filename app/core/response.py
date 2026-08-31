from datetime import datetime, timezone
from typing import Any


def ocpi_response(
    data: Any = None,
    status_code: int = 1000,
    status_message: str | None = None,
) -> dict:
    """
    Create a standard OCPI response envelope.
    """

    return {
        "data": data,
        "status_code": status_code,
        "status_message": status_message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }