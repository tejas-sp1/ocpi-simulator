from datetime import datetime

from fastapi import APIRouter, Header, HTTPException, Query, Response

from app.core.response import OCPIResponse, create_ocpi_response

from app.modules.locations.schemas import (
    Connector,
    EVSE,
    Location,
    LocationPatch,
    EVSEPatch
)

from app.modules.locations.service import (
    get_all_locations,
    get_connector,
    get_evse,
    get_location,
    patch_evse,
    patch_location,
    update_connector,
    update_evse,
    update_location,
)

router = APIRouter(
    prefix="/ocpi",
    tags=["Locations"],
)


# =========================================================
# CPO - Locations Sender Interface
# =========================================================


@router.get(
    "/cpo/2.2.1/locations",
    response_model=OCPIResponse[list[Location]],
)
def get_cpo_locations(
    response: Response,
    x_request_id: str = Header(
        ...,
        alias="X-Request-ID",
    ),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
    date_from: datetime | None = Query(
        default=None,
        description="Only return Locations updated on or after this date/time.",
    ),
    date_to: datetime | None = Query(
        default=None,
        description="Only return Locations updated before this date/time.",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        description="Maximum number of Locations to return.",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of Locations to skip.",
    ),
):
    """
    Fetch a paginated list of Locations.

    Supports optional filtering by last_updated
    using date_from and date_to.
    """

    # Validate date range
    if (
        date_from is not None
        and date_to is not None
        and date_from >= date_to
    ):
        raise HTTPException(
            status_code=400,
            detail="date_from must be earlier than date_to.",
        )

    all_locations = get_all_locations()

    # =====================================================
    # Date filtering
    # =====================================================

    filtered_locations: list[Location] = []

    for location in all_locations:

        if (
            date_from is not None
            and location.last_updated < date_from
        ):
            continue

        if (
            date_to is not None
            and location.last_updated >= date_to
        ):
            continue

        filtered_locations.append(location)

    # =====================================================
    # Pagination
    # =====================================================

    total_count = len(filtered_locations)

    paginated_locations = filtered_locations[
        offset: offset + limit
    ]

    # =====================================================
    # Pagination headers
    # =====================================================

    response.headers["X-Total-Count"] = str(total_count)
    response.headers["X-Limit"] = str(limit)
    response.headers["X-Offset"] = str(offset)

    # =====================================================
    # OCPI response
    # =====================================================

    return create_ocpi_response(
        data=paginated_locations,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


# =========================================================
# CPO - Get one Location
# =========================================================


@router.get(
    "/cpo/2.2.1/locations/{location_id}",
    response_model=OCPIResponse[Location],
)
def get_cpo_location(
    location_id: str,
    response: Response,
    x_request_id: str = Header(
        ...,
        alias="X-Request-ID",
    ),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Retrieve one Location by location_id.
    """

    location = get_location(location_id)

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found.",
        )

    return create_ocpi_response(
        data=location,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


# =========================================================
# CPO - Get one EVSE
# =========================================================


@router.get(
    "/cpo/2.2.1/locations/{location_id}/{evse_uid}",
    response_model=OCPIResponse[EVSE],
)
def get_cpo_evse(
    location_id: str,
    evse_uid: str,
    response: Response,
    x_request_id: str = Header(
        ...,
        alias="X-Request-ID",
    ),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Retrieve one EVSE from a Location.
    """

    evse = get_evse(
        location_id=location_id,
        evse_uid=evse_uid,
    )

    if evse is None:
        raise HTTPException(
            status_code=404,
            detail="EVSE not found.",
        )

    return create_ocpi_response(
        data=evse,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


# =========================================================
# CPO - Get one Connector
# =========================================================


@router.get(
    "/cpo/2.2.1/locations/{location_id}/{evse_uid}/{connector_id}",
    response_model=OCPIResponse[Connector],
)
def get_cpo_connector(
    location_id: str,
    evse_uid: str,
    connector_id: str,
    response: Response,
    x_request_id: str = Header(
        ...,
        alias="X-Request-ID",
    ),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Retrieve one Connector from an EVSE.
    """

    connector = get_connector(
        location_id=location_id,
        evse_uid=evse_uid,
        connector_id=connector_id,
    )

    if connector is None:
        raise HTTPException(
            status_code=404,
            detail="Connector not found.",
        )

    return create_ocpi_response(
        data=connector,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )


# =========================================================
# eMSP - Locations Receiver Interface
# =========================================================


@router.put(
    "/emsp/2.2.1/locations/{country_code}/{party_id}/{location_id}",
    response_model=OCPIResponse[Location],
)
def put_emsp_location(
    country_code: str,
    party_id: str,
    location_id: str,
    location: Location,
    response: Response,
    x_request_id: str = Header(
        ...,
        alias="X-Request-ID",
    ),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Create or replace a Location received from a CPO.
    """

    # =====================================================
    # Validate path against body
    # =====================================================

    if location.country_code != country_code:
        raise HTTPException(
            status_code=400,
            detail="Country code does not match location data.",
        )

    if location.party_id != party_id:
        raise HTTPException(
            status_code=400,
            detail="Party ID does not match location data.",
        )

    if location.id != location_id:
        raise HTTPException(
            status_code=400,
            detail="Location ID does not match location data.",
        )

    updated = update_location(location)

    return create_ocpi_response(
        data=updated,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )
# =========================================================
# eMSP - EVSE Receiver Interface
# =========================================================


@router.put(
    "/emsp/2.2.1/locations/{country_code}/{party_id}/{location_id}/{evse_uid}",
    response_model=OCPIResponse[EVSE],
)
def put_emsp_evse(
    country_code: str,
    party_id: str,
    location_id: str,
    evse_uid: str,
    evse: EVSE,
    response: Response,
    x_request_id: str = Header(
        ...,
        alias="X-Request-ID",
    ),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Create or replace an EVSE received from a CPO.
    """

    # -----------------------------------------------------
    # Find parent Location
    # -----------------------------------------------------

    location = get_location(location_id)

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found.",
        )

    # -----------------------------------------------------
    # Validate owning CPO information
    # -----------------------------------------------------

    if location.country_code != country_code:
        raise HTTPException(
            status_code=400,
            detail="Country code does not match Location data.",
        )

    if location.party_id != party_id:
        raise HTTPException(
            status_code=400,
            detail="Party ID does not match Location data.",
        )

    # -----------------------------------------------------
    # Validate EVSE UID
    # -----------------------------------------------------

    if evse.uid != evse_uid:
        raise HTTPException(
            status_code=400,
            detail="EVSE UID does not match EVSE data.",
        )

    # -----------------------------------------------------
    # Create or replace EVSE
    # -----------------------------------------------------

    updated_evse = update_evse(
        location_id=location_id,
        evse=evse,
    )

    if updated_evse is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found.",
        )

    # -----------------------------------------------------
    # Return OCPI response
    # -----------------------------------------------------

    return create_ocpi_response(
        data=updated_evse,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )

# =========================================================
# eMSP - Connector Receiver Interface
# =========================================================


@router.put(
    "/emsp/2.2.1/locations/{country_code}/{party_id}/{location_id}/{evse_uid}/{connector_id}",
    response_model=OCPIResponse[Connector],
)
def put_emsp_connector(
    country_code: str,
    party_id: str,
    location_id: str,
    evse_uid: str,
    connector_id: str,
    connector: Connector,
    response: Response,
    x_request_id: str = Header(
        ...,
        alias="X-Request-ID",
    ),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Create or replace a Connector received from a CPO.
    """

    # -----------------------------------------------------
    # Find parent Location
    # -----------------------------------------------------

    location = get_location(location_id)

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found.",
        )

    # -----------------------------------------------------
    # Validate CPO information
    # -----------------------------------------------------

    if location.country_code != country_code:
        raise HTTPException(
            status_code=400,
            detail="Country code does not match Location data.",
        )

    if location.party_id != party_id:
        raise HTTPException(
            status_code=400,
            detail="Party ID does not match Location data.",
        )

    # -----------------------------------------------------
    # Find parent EVSE
    # -----------------------------------------------------

    evse = get_evse(
        location_id=location_id,
        evse_uid=evse_uid,
    )

    if evse is None:
        raise HTTPException(
            status_code=404,
            detail="EVSE not found.",
        )

    # -----------------------------------------------------
    # Validate Connector ID
    # -----------------------------------------------------

    if connector.id != connector_id:
        raise HTTPException(
            status_code=400,
            detail="Connector ID does not match Connector data.",
        )

    # -----------------------------------------------------
    # Create or replace Connector
    # -----------------------------------------------------

    updated_connector = update_connector(
        location_id=location_id,
        evse_uid=evse_uid,
        connector=connector,
    )

    if updated_connector is None:
        raise HTTPException(
            status_code=404,
            detail="Location or EVSE not found.",
        )

    # -----------------------------------------------------
    # Return OCPI response
    # -----------------------------------------------------

    return create_ocpi_response(
        data=updated_connector,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )

# =========================================================
# eMSP - Location PATCH Receiver Interface
# =========================================================


@router.patch(
    "/emsp/2.2.1/locations/{country_code}/{party_id}/{location_id}",
    response_model=OCPIResponse[None],
)
def patch_emsp_location(
    country_code: str,
    party_id: str,
    location_id: str,
    patch: LocationPatch,
    response: Response,
    x_request_id: str = Header(
        ...,
        alias="X-Request-ID",
    ),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Apply a partial update to a Location received from a CPO.
    """

    # -----------------------------------------------------
    # Find Location
    # -----------------------------------------------------

    location = get_location(location_id)

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found.",
        )

    # -----------------------------------------------------
    # Validate country code
    # -----------------------------------------------------

    if location.country_code != country_code:
        raise HTTPException(
            status_code=400,
            detail="Country code does not match Location data.",
        )

    # -----------------------------------------------------
    # Validate party ID
    # -----------------------------------------------------

    if location.party_id != party_id:
        raise HTTPException(
            status_code=400,
            detail="Party ID does not match Location data.",
        )

    # -----------------------------------------------------
    # Apply PATCH
    # -----------------------------------------------------

    updated = patch_location(
        location_id=location_id,
        patch=patch,
    )

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found.",
        )

    # -----------------------------------------------------
    # PATCH response
    # -----------------------------------------------------

    return create_ocpi_response(
        data=None,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )



# =========================================================
# eMSP - EVSE PATCH Receiver Interface
# =========================================================


@router.patch(
    "/emsp/2.2.1/locations/{country_code}/{party_id}/{location_id}/{evse_uid}",
    response_model=OCPIResponse[None],
)
def patch_emsp_evse(
    country_code: str,
    party_id: str,
    location_id: str,
    evse_uid: str,
    patch: EVSEPatch,
    response: Response,
    x_request_id: str = Header(
        ...,
        alias="X-Request-ID",
    ),
    x_correlation_id: str = Header(
        ...,
        alias="X-Correlation-ID",
    ),
):
    """
    Apply a partial update to an EVSE received from a CPO.
    """

    # -----------------------------------------------------
    # Find Location
    # -----------------------------------------------------

    location = get_location(location_id)

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found.",
        )

    # -----------------------------------------------------
    # Validate country code
    # -----------------------------------------------------

    if location.country_code != country_code:
        raise HTTPException(
            status_code=400,
            detail="Country code does not match Location data.",
        )

    # -----------------------------------------------------
    # Validate party ID
    # -----------------------------------------------------

    if location.party_id != party_id:
        raise HTTPException(
            status_code=400,
            detail="Party ID does not match Location data.",
        )

    # -----------------------------------------------------
    # Find EVSE
    # -----------------------------------------------------

    evse = get_evse(
        location_id=location_id,
        evse_uid=evse_uid,
    )

    if evse is None:
        raise HTTPException(
            status_code=404,
            detail="EVSE not found.",
        )

    # -----------------------------------------------------
    # Apply PATCH
    # -----------------------------------------------------

    updated = patch_evse(
        location_id=location_id,
        evse_uid=evse_uid,
        patch=patch,
    )

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail="EVSE not found.",
        )

    # -----------------------------------------------------
    # Return OCPI response
    # -----------------------------------------------------

    return create_ocpi_response(
        data=None,
        response=response,
        request_id=x_request_id,
        correlation_id=x_correlation_id,
    )