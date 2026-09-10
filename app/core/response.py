from datetime import datetime, timezone
from typing import Generic, TypeVar

from fastapi import Response
from pydantic import BaseModel


T = TypeVar("T")


class OCPIResponse(BaseModel, Generic[T]):
    status_code: int
    status_message: str | None = None
    timestamp: datetime
    data: T

    model_config = {
        "json_schema_extra": {
            "example": {
                "status_code": 1000,
                "status_message": "Success",
                "timestamp": "2026-09-11T00:00:00Z",
                "data": None,
            }
        }
    }


def create_ocpi_response(
    data: T,
    response: Response,
    request_id: str,
    correlation_id: str,
    status_code: int = 1000,
    status_message: str = "Success",
) -> OCPIResponse[T]:

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Correlation-ID"] = correlation_id

    return OCPIResponse(
        status_code=status_code,
        status_message=status_message,
        timestamp=datetime.now(timezone.utc),
        data=data,
    )