from datetime import datetime, timezone

from app.modules.locations.schemas import (
    BusinessDetails,
    Connector,
    ConnectorFormat,
    ConnectorPatch,
    ConnectorType,
    EVSE,
    EVSEPatch,
    EVSEStatus,
    GeoLocation,
    Location,
    LocationPatch,
    PowerType,
)

# =========================================================
# In-memory location storage
# =========================================================

locations: dict[str, Location] = {}


# =========================================================
# Sample location
# =========================================================

def create_sample_location() -> Location:
    """
    Create a sample charging location for simulator testing.
    """

    now = datetime.now(timezone.utc)

    return Location(
        country_code="IN",
        party_id="TSP",
        id="LOC001",
        publish=True,
        name="OCPI Simulator Charging Hub",
        address="Bangalore-Mysore Road",
        city="Bengaluru",
        postal_code="560026",
        state="Karnataka",
        country="IND",
        coordinates=GeoLocation(
            latitude="12.971599",
            longitude="77.594566",
        ),
        evses=[
            EVSE(
                uid="EVSE001",
                evse_id="IN*TSP*E001",
                status=EVSEStatus.AVAILABLE,
                connectors=[
                    Connector(
                        id="1",
                        standard=ConnectorType.IEC_62196_T2,
                        format=ConnectorFormat.SOCKET,
                        power_type=PowerType.AC_3_PHASE,
                        max_voltage=400,
                        max_amperage=32,
                        max_electric_power=22000,
                        last_updated=now,
                    )
                ],
                coordinates=GeoLocation(
                    latitude="12.971599",
                    longitude="77.594566",
                ),
                last_updated=now,
            )
        ],
        operator=BusinessDetails(
            name="OCPI Simulator"
        ),
        time_zone="Asia/Kolkata",
        charging_when_closed=True,
        last_updated=now,
    )


# =========================================================
# Initialize sample data
# =========================================================

sample_location = create_sample_location()
locations[sample_location.id] = sample_location


# =========================================================
# Location operations
# =========================================================

def get_all_locations() -> list[Location]:
    """
    Return all stored locations.
    """
    return list(locations.values())


def get_location(location_id: str) -> Location | None:
    """
    Return a location by its ID.
    """
    return locations.get(location_id)


def get_evse(
    location_id: str,
    evse_uid: str,
) -> EVSE | None:
    """
    Return a specific EVSE from a location.
    """

    location = locations.get(location_id)

    if location is None or location.evses is None:
        return None

    for evse in location.evses:
        if evse.uid == evse_uid:
            return evse

    return None


def update_evse(
    location_id: str,
    evse: EVSE,
) -> EVSE | None:
    """
    Create or replace an EVSE inside an existing Location.

    Returns:
        The updated EVSE when the Location exists.
        None when the Location does not exist.
    """

    location = locations.get(location_id)

    if location is None:
        return None

    if location.evses is None:
        location.evses = []

    # Replace an existing EVSE with the same UID.
    for index, existing_evse in enumerate(location.evses):
        if existing_evse.uid == evse.uid:
            location.evses[index] = evse

            # The parent Location was updated because
            # one of its EVSEs was updated.
            location.last_updated = evse.last_updated

            return evse

    # EVSE does not exist, so create it.
    location.evses.append(evse)

    # The parent Location was updated because
    # a new EVSE was added.
    location.last_updated = evse.last_updated

    return evse



def patch_evse(
    location_id: str,
    evse_uid: str,
    patch: EVSEPatch,
) -> EVSE | None:
    """
    Apply a partial update to an existing EVSE.

    Only fields explicitly supplied in the PATCH request
    are changed.

    The parent Location timestamp is also updated.
    """

    evse = get_evse(
        location_id=location_id,
        evse_uid=evse_uid,
    )

    if evse is None:
        return None

    changes = patch.model_dump(
        exclude_unset=True
    )

    new_last_updated = changes.pop("last_updated")

    for field_name, value in changes.items():
        setattr(
            evse,
            field_name,
            value,
        )

    # PATCH requires the EVSE timestamp to change.
    evse.last_updated = new_last_updated

    # OCPI requires the parent Location timestamp
    # to be updated when an EVSE is patched.
    location = locations.get(location_id)

    if location is not None:
        location.last_updated = new_last_updated

    return evse



def get_connector(
    location_id: str,
    evse_uid: str,
    connector_id: str,
) -> Connector | None:
    """
    Return a specific connector from an EVSE.
    """

    evse = get_evse(
        location_id=location_id,
        evse_uid=evse_uid,
    )

    if evse is None:
        return None

    for connector in evse.connectors:
        if connector.id == connector_id:
            return connector

    return None


def update_connector(
    location_id: str,
    evse_uid: str,
    connector: Connector,
) -> Connector | None:
    """
    Create or replace a Connector inside an existing EVSE.

    Returns:
        The updated Connector when the Location and EVSE exist.
        None when the Location or EVSE does not exist.
    """

    evse = get_evse(
        location_id=location_id,
        evse_uid=evse_uid,
    )

    if evse is None:
        return None

    for index, existing_connector in enumerate(evse.connectors):
        if existing_connector.id == connector.id:
            evse.connectors[index] = connector

            # The EVSE and its parent Location were updated.
            evse.last_updated = connector.last_updated

            location = locations.get(location_id)

            if location is not None:
                location.last_updated = connector.last_updated

            return connector

    # Connector does not exist, so create it.
    evse.connectors.append(connector)

    # Update timestamps.
    evse.last_updated = connector.last_updated

    location = locations.get(location_id)

    if location is not None:
        location.last_updated = connector.last_updated

    return connector


def patch_connector(
    location_id: str,
    evse_uid: str,
    connector_id: str,
    patch: ConnectorPatch,
) -> Connector | None:
    """
    Apply a partial update to an existing Connector.

    Only fields explicitly supplied in the PATCH request
    are changed.

    When a Connector is patched:
    - Connector.last_updated is updated.
    - Parent EVSE.last_updated is updated.
    - Parent Location.last_updated is updated.
    """

    connector = get_connector(
        location_id=location_id,
        evse_uid=evse_uid,
        connector_id=connector_id,
    )

    if connector is None:
        return None

    changes = patch.model_dump(
        exclude_unset=True
    )

    new_last_updated = changes.pop("last_updated")

    # Apply only the supplied fields.
    for field_name, value in changes.items():
        setattr(
            connector,
            field_name,
            value,
        )

    # Update Connector timestamp.
    connector.last_updated = new_last_updated

    # Find the parent EVSE.
    evse = get_evse(
        location_id=location_id,
        evse_uid=evse_uid,
    )

    if evse is not None:
        # OCPI requires parent EVSE timestamp update.
        evse.last_updated = new_last_updated

    # Find the parent Location.
    location = locations.get(location_id)

    if location is not None:
        # OCPI requires parent Location timestamp update.
        location.last_updated = new_last_updated

    return connector


def create_location(location: Location) -> Location:
    """
    Add a new location.
    """

    locations[location.id] = location

    return location


def update_location(
    location: Location,
) -> Location:
    """
    Replace an existing location.
    """

    locations[location.id] = location

    return location


def patch_location(
    location_id: str,
    patch: LocationPatch,
) -> Location | None:
    """
    Apply a partial update to an existing Location.

    Only fields explicitly included in the PATCH request
    are changed.

    last_updated is always updated because it is mandatory
    in an OCPI PATCH request.
    """

    location = locations.get(location_id)

    if location is None:
        return None

    # Get only the fields actually supplied by the client.
    changes = patch.model_dump(
        exclude_unset=True
    )

    # last_updated must always be present.
    new_last_updated = changes.pop("last_updated")

    # Apply only supplied fields.
    for field_name, value in changes.items():
        setattr(
            location,
            field_name,
            value,
        )

    # Update Location timestamp.
    location.last_updated = new_last_updated

    return location


def delete_location(
    location_id: str,
) -> bool:
    """
    Delete a location.

    Returns True when deleted.
    Returns False when the location does not exist.
    """

    if location_id not in locations:
        return False

    del locations[location_id]

    return True