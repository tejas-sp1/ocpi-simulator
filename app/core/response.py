from datetime import datetime, timezone
from typing import Any

from fastapi import Response
from pydantic import BaseModel


class OCPIResponse(BaseModel):
    status_code: int
    status_message: str | None = None
    timestamp: datetime
    data: Any = None


def create_ocpi_response(
    data: Any,
    response: Response,
    request_id: str,
    correlation_id: str,
    status_code: int = 1000,
    status_message: str = "Success",
) -> OCPIResponse:

    # Return the same request and correlation IDs
    # that were received in the request.
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Correlation-ID"] = correlation_id

    return OCPIResponse(
        status_code=status_code,
        status_message=status_message,
        timestamp=datetime.now(timezone.utc),
        data=data,
    )