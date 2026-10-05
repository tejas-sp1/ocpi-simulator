from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass
from secrets import token_hex
from typing import Any
from uuid import uuid4

import httpx
from pydantic import HttpUrl

from app.modules.credentials.schemas import (
    BusinessDetails,
    Credentials,
    CredentialsRole,
    Role,
)


SUPPORTED_VERSION = "2.2.1"


@dataclass
class RemoteCpoConnection:
    versions_url: str
    token_a: str
    version: str
    version_url: str
    credentials_url: str
    locations_url: str | None
    returned_credentials: Credentials


connection: RemoteCpoConnection | None = None


def build_ocpi_authorization(token: str) -> str:
    encoded = b64encode(token.encode("utf-8")).decode("ascii")
    return f"Token {encoded}"


def build_headers(
    token: str,
    *,
    correlation_id: str | None = None,
    include_content_type: bool = False,
) -> dict[str, str]:
    headers = {
        "Authorization": build_ocpi_authorization(token),
        "X-Request-ID": str(uuid4()),
        "X-Correlation-ID": correlation_id or str(uuid4()),
        "Accept": "application/json",
    }
    if include_content_type:
        headers["Content-Type"] = "application/json"
    return headers


def _parse_ocpi_response(response: httpx.Response, label: str) -> dict[str, Any]:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"{label} failed with HTTP {response.status_code}: {response.text[:500]}"
        ) from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"{label} returned invalid JSON.") from exc

    if payload.get("status_code") != 1000:
        raise RuntimeError(
            f"{label} returned OCPI status {payload.get('status_code')}: "
            f"{payload.get('status_message', 'Unknown error')}"
        )

    return payload


def _find_endpoint(
    endpoints: list[dict[str, Any]],
    identifier: str,
    role: str | None = None,
) -> dict[str, Any] | None:
    for endpoint in endpoints:
        if str(endpoint.get("identifier", "")).lower() != identifier.lower():
            continue
        if role is not None and str(endpoint.get("role", "")).upper() != role.upper():
            continue
        if endpoint.get("url"):
            return endpoint
    return None


def _build_emsp_credentials(
    *,
    versions_url: str,
    party_id: str,
    country_code: str,
    business_name: str,
) -> Credentials:
    # Token B is the token the remote CPO will use to call us after registration.
    token_b = token_hex(32)

    return Credentials(
        token=token_b,
        url=HttpUrl(versions_url),
        roles=[
            CredentialsRole(
                role=Role.EMSP,
                business_details=BusinessDetails(name=business_name),
                party_id=party_id,
                country_code=country_code,
            )
        ],
    )


async def handshake_with_cpo(
    *,
    versions_url: str,
    token_a: str,
    emsp_versions_url: str,
    party_id: str = "TSP",
    country_code: str = "IN",
    business_name: str = "TejasSP",
) -> dict[str, Any]:
    """
    Act as an OCPI client toward a remote CPO and perform registration.

    Flow:
        1. GET remote CPO /versions using Token A.
        2. Select OCPI 2.2.1.
        3. GET remote CPO version details using Token A.
        4. Discover the CPO Credentials RECEIVER endpoint.
        5. Generate Token B and POST our eMSP Credentials using Token A.
        6. Receive Token C from the CPO and store it for future requests.
        7. Discover and store the CPO Locations SENDER endpoint.
    """
    global connection

    versions_url = versions_url.rstrip("/")
    token_a = token_a.strip()
    emsp_versions_url = emsp_versions_url.rstrip("/")

    if not token_a:
        raise ValueError("Bootstrap Token A is required.")

    correlation_id = str(uuid4())
    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        versions_response = await client.get(
            versions_url,
            headers=build_headers(token_a, correlation_id=correlation_id),
        )
        versions_payload = _parse_ocpi_response(
            versions_response,
            "CPO /versions",
        )

        versions = versions_payload.get("data") or []
        selected = next(
            (item for item in versions if item.get("version") == SUPPORTED_VERSION),
            None,
        )
        if not selected:
            available = ", ".join(str(item.get("version")) for item in versions)
            raise RuntimeError(
                f"CPO does not advertise OCPI {SUPPORTED_VERSION}. "
                f"Available versions: {available or 'none'}"
            )

        version_url = str(selected.get("url") or "").rstrip("/")
        if not version_url:
            raise RuntimeError("CPO returned no URL for OCPI 2.2.1.")

        version_response = await client.get(
            version_url,
            headers=build_headers(token_a, correlation_id=correlation_id),
        )
        version_payload = _parse_ocpi_response(
            version_response,
            "CPO 2.2.1 version details",
        )

        version_data = version_payload.get("data") or {}
        endpoints = version_data.get("endpoints") or []
        if not isinstance(endpoints, list):
            raise RuntimeError("CPO version details contain an invalid endpoints list.")

        credentials_endpoint = _find_endpoint(
            endpoints,
            "credentials",
            "RECEIVER",
        )
        if credentials_endpoint is None:
            raise RuntimeError(
                "CPO 2.2.1 endpoint map does not expose a Credentials RECEIVER endpoint."
            )

        credentials_url = str(credentials_endpoint["url"])

        locations_endpoint = _find_endpoint(
            endpoints,
            "locations",
            "SENDER",
        )
        locations_url = (
            str(locations_endpoint["url"])
            if locations_endpoint is not None
            else None
        )

        emsp_credentials = _build_emsp_credentials(
            versions_url=emsp_versions_url,
            party_id=party_id,
            country_code=country_code,
            business_name=business_name,
        )

        credentials_response = await client.post(
            credentials_url,
            headers=build_headers(
                token_a,
                correlation_id=correlation_id,
                include_content_type=True,
            ),
            json=emsp_credentials.model_dump(mode="json"),
        )

        if credentials_response.status_code == 405:
            raise RuntimeError(
                "CPO reports that this client is already registered (HTTP 405). "
                "Use a fresh CPO bootstrap Token A or unregister the existing client on the CPO side."
            )

        credentials_payload = _parse_ocpi_response(
            credentials_response,
            "CPO Credentials POST",
        )

        returned = credentials_payload.get("data")
        if not returned:
            raise RuntimeError("CPO Credentials response did not contain returned credentials (Token C).")

        returned_credentials = Credentials.model_validate(returned)

        connection = RemoteCpoConnection(
            versions_url=versions_url,
            token_a=token_a,
            version=SUPPORTED_VERSION,
            version_url=version_url,
            credentials_url=credentials_url,
            locations_url=locations_url,
            returned_credentials=returned_credentials,
        )

    return get_connection_summary()


def mask_token(token: str | None) -> str | None:
    if not token:
        return None
    if len(token) <= 8:
        return "•" * len(token)
    return f"{'•' * 12}{token[-6:]}"


def get_connection_summary() -> dict[str, Any]:
    if connection is None:
        return {
            "connected": False,
            "role": "EMSP",
            "version": None,
            "remote_versions_url": None,
            "remote_version_url": None,
            "credentials_url": None,
            "locations_url": None,
            "remote_cpo": None,
            "token_c_masked": None,
        }

    role = connection.returned_credentials.roles[0] if connection.returned_credentials.roles else None
    business = role.business_details if role else None

    return {
        "connected": True,
        "role": "EMSP",
        "version": connection.version,
        "remote_versions_url": connection.versions_url,
        "remote_version_url": connection.version_url,
        "credentials_url": connection.credentials_url,
        "locations_url": connection.locations_url,
        "remote_cpo": {
            "name": business.name if business else None,
            "party_id": role.party_id if role else None,
            "country_code": role.country_code if role else None,
        },
        "token_c_masked": mask_token(connection.returned_credentials.token),
    }


async def fetch_cpo_locations() -> list[dict[str, Any]]:
    if connection is None:
        raise RuntimeError("No CPO connection exists. Complete the handshake first.")

    if not connection.locations_url:
        raise RuntimeError("The CPO version endpoint map does not expose a Locations SENDER endpoint.")

    token_c = connection.returned_credentials.token
    correlation_id = str(uuid4())

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        follow_redirects=True,
    ) as client:
        response = await client.get(
            connection.locations_url,
            params={"limit": 50, "offset": 0},
            headers=build_headers(
                token_c,
                correlation_id=correlation_id,
            ),
        )
        payload = _parse_ocpi_response(
            response,
            "CPO Locations GET",
        )

    data = payload.get("data") or []
    if not isinstance(data, list):
        raise RuntimeError("CPO Locations response did not contain a list.")
    return data


def clear_connection() -> None:
    global connection
    connection = None
