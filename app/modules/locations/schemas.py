from datetime import datetime, time, date
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl

from datetime import datetime

from pydantic import BaseModel


class LocationPatch(BaseModel):
    """
    Partial update for a Location.

    Only fields included in the request will be changed.
    last_updated is mandatory for every PATCH request.
    """

    publish: bool | None = None
    name: str | None = None
    address: str | None = None
    city: str | None = None
    postal_code: str | None = None
    state: str | None = None
    country: str | None = None
    coordinates: GeoLocation | None = None
    operator: BusinessDetails | None = None
    time_zone: str | None = None
    charging_when_closed: bool | None = None

    last_updated: datetime
# =========================================================
# ENUMS
# =========================================================


class PublishTokenType(str, Enum):
    AD_HOC_USER = "AD_HOC_USER"
    APP_USER = "APP_USER"
    OTHER = "OTHER"
    RFID = "RFID"


class ParkingType(str, Enum):
    ALONG_MOTORWAY = "ALONG_MOTORWAY"
    PARKING_GARAGE = "PARKING_GARAGE"
    PARKING_LOT = "PARKING_LOT"
    ON_DRIVEWAY = "ON_DRIVEWAY"
    ON_STREET = "ON_STREET"
    UNDERGROUND_GARAGE = "UNDERGROUND_GARAGE"


class ParkingRestriction(str, Enum):
    EV_ONLY = "EV_ONLY"
    PLUGGED = "PLUGGED"
    DISABLED = "DISABLED"
    CUSTOMERS = "CUSTOMERS"
    MOTORCYCLES = "MOTORCYCLES"


class EVSEStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    BLOCKED = "BLOCKED"
    CHARGING = "CHARGING"
    INOPERATIVE = "INOPERATIVE"
    OUTOFORDER = "OUTOFORDER"
    PLANNED = "PLANNED"
    REMOVED = "REMOVED"
    RESERVED = "RESERVED"
    UNKNOWN = "UNKNOWN"
    UNREACHABLE = "UNREACHABLE"


class ConnectorType(str, Enum):
    CHADEMO = "CHADEMO"
    DOMESTIC_A = "DOMESTIC_A"
    DOMESTIC_B = "DOMESTIC_B"
    DOMESTIC_C = "DOMESTIC_C"
    DOMESTIC_D = "DOMESTIC_D"
    DOMESTIC_E = "DOMESTIC_E"
    DOMESTIC_F = "DOMESTIC_F"
    DOMESTIC_G = "DOMESTIC_G"
    DOMESTIC_H = "DOMESTIC_H"
    DOMESTIC_I = "DOMESTIC_I"
    DOMESTIC_J = "DOMESTIC_J"
    DOMESTIC_K = "DOMESTIC_K"
    DOMESTIC_L = "DOMESTIC_L"

    IEC_60309_2_SINGLE_16 = "IEC_60309_2_SINGLE_16"
    IEC_60309_2_THREE_16 = "IEC_60309_2_THREE_16"
    IEC_60309_2_THREE_32 = "IEC_60309_2_THREE_32"
    IEC_60309_2_THREE_64 = "IEC_60309_2_THREE_64"

    IEC_62196_T1 = "IEC_62196_T1"
    IEC_62196_T1_COMBO = "IEC_62196_T1_COMBO"
    IEC_62196_T2 = "IEC_62196_T2"
    IEC_62196_T2_COMBO = "IEC_62196_T2_COMBO"
    IEC_62196_T3A = "IEC_62196_T3A"
    IEC_62196_T3C = "IEC_62196_T3C"

    NEMA_5_20 = "NEMA_5_20"
    NEMA_6_30 = "NEMA_6_30"
    NEMA_6_50 = "NEMA_6_50"
    NEMA_10_30 = "NEMA_10_30"
    NEMA_10_50 = "NEMA_10_50"
    NEMA_14_30 = "NEMA_14_30"
    NEMA_14_50 = "NEMA_14_50"

    PANTOGRAPH_BOTTOM_UP = "PANTOGRAPH_BOTTOM_UP"
    PANTOGRAPH_TOP_DOWN = "PANTOGRAPH_TOP_DOWN"

    TESLA_R = "TESLA_R"
    TESLA_S = "TESLA_S"


class ConnectorFormat(str, Enum):
    SOCKET = "SOCKET"
    CABLE = "CABLE"


class PowerType(str, Enum):
    AC_1_PHASE = "AC_1_PHASE"
    AC_2_PHASE = "AC_2_PHASE"
    AC_2_PHASE_SPLIT = "AC_2_PHASE_SPLIT"
    AC_3_PHASE = "AC_3_PHASE"
    DC = "DC"


class Capability(str, Enum):
    CHARGING_PROFILE_CAPABLE = "CHARGING_PROFILE_CAPABLE"
    CHARGING_PREFERENCES_CAPABLE = "CHARGING_PREFERENCES_CAPABLE"
    CHIP_CARD_SUPPORT = "CHIP_CARD_SUPPORT"
    CONTACTLESS_CARD_SUPPORT = "CONTACTLESS_CARD_SUPPORT"
    CREDIT_CARD_PAYABLE = "CREDIT_CARD_PAYABLE"
    DEBIT_CARD_PAYABLE = "DEBIT_CARD_PAYABLE"
    PEDAL_BICYCLE = "PEDAL_BICYCLE"
    REMOTE_START_STOP_CAPABLE = "REMOTE_START_STOP_CAPABLE"
    RESERVABLE = "RESERVABLE"
    RFID_READER = "RFID_READER"
    START_SESSION_CONNECTOR_REQUIRED = "START_SESSION_CONNECTOR_REQUIRED"
    UNLOCK_CAPABLE = "UNLOCK_CAPABLE"


class Facility(str, Enum):
    HOTEL = "HOTEL"
    RESTAURANT = "RESTAURANT"
    CAFE = "CAFE"
    MALL = "MALL"
    SUPERMARKET = "SUPERMARKET"
    SPORT = "SPORT"
    RECREATION_AREA = "RECREATION_AREA"
    NATURE = "NATURE"
    MUSEUM = "MUSEUM"
    BIKE_SHARING = "BIKE_SHARING"
    BUS_STOP = "BUS_STOP"
    TAXI_STAND = "TAXI_STAND"
    TRAM_STOP = "TRAM_STOP"
    METRO_STATION = "METRO_STATION"
    TRAIN_STATION = "TRAIN_STATION"
    AIRPORT = "AIRPORT"
    PARKING_LOT = "PARKING_LOT"
    CARPOOL_PARKING = "CARPOOL_PARKING"
    FUEL_STATION = "FUEL_STATION"
    WIFI = "WIFI"


class ImageCategory(str, Enum):
    CHARGER = "CHARGER"
    ENTRANCE = "ENTRANCE"
    LOCATION = "LOCATION"
    NETWORK = "NETWORK"
    OPERATOR = "OPERATOR"
    OTHER = "OTHER"


class EnergySourceCategory(str, Enum):
    NUCLEAR = "NUCLEAR"
    GENERAL_FOSSIL = "GENERAL_FOSSIL"
    COAL = "COAL"
    GAS = "GAS"
    GENERAL_GREEN = "GENERAL_GREEN"
    SOLAR = "SOLAR"
    WIND = "WIND"
    WATER = "WATER"


class EnvironmentalImpactCategory(str, Enum):
    NUCLEAR_WASTE = "NUCLEAR_WASTE"
    CARBON_DIOXIDE = "CARBON_DIOXIDE"


# =========================================================
# BASIC / REUSABLE OBJECTS
# =========================================================


class DisplayText(BaseModel):
    language: str = Field(
        min_length=2,
        max_length=2,
    )
    text: str = Field(
        max_length=512,
    )


class GeoLocation(BaseModel):
    latitude: str
    longitude: str


class AdditionalGeoLocation(BaseModel):
    latitude: str
    longitude: str
    name: DisplayText | None = None


class PublishToken(BaseModel):
    uid: str = Field(max_length=36)
    type: PublishTokenType


class BusinessDetails(BaseModel):
    name: str = Field(max_length=100)
    website: HttpUrl | None = None


class Image(BaseModel):
    url: HttpUrl
    thumbnail: HttpUrl | None = None
    category: ImageCategory
    type: str
    width: int | None = None
    height: int | None = None


# =========================================================
# OPENING HOURS
# =========================================================


class RegularHours(BaseModel):
    weekday: list[int] = Field(
        min_length=1
    )
    period_begin: time
    period_end: time


class ExceptionalPeriod(BaseModel):
    period_begin: datetime
    period_end: datetime


class Hours(BaseModel):
    twentyfourseven: bool
    regular_hours: list[RegularHours] | None = None
    exceptional_openings: list[ExceptionalPeriod] | None = None
    exceptional_closings: list[ExceptionalPeriod] | None = None


# =========================================================
# STATUS SCHEDULE
# =========================================================


class StatusSchedule(BaseModel):
    period_begin: datetime
    period_end: datetime | None = None
    status: EVSEStatus


# =========================================================
# ENERGY MIX
# =========================================================


class EnergySource(BaseModel):
    source: EnergySourceCategory
    percentage: float


class EnvironmentalImpact(BaseModel):
    category: EnvironmentalImpactCategory
    amount: float


class EnergyMix(BaseModel):
    is_green_energy: bool
    energy_sources: list[EnergySource] | None = None
    environ_impact: list[EnvironmentalImpact] | None = None
    supplier_name: str | None = Field(
        default=None,
        max_length=64,
    )
    energy_product_name: str | None = Field(
        default=None,
        max_length=64,
    )


# =========================================================
# CONNECTOR
# =========================================================


class Connector(BaseModel):
    id: str = Field(max_length=36)

    standard: ConnectorType

    format: ConnectorFormat

    power_type: PowerType

    max_voltage: int

    max_amperage: int

    max_electric_power: int | None = None

    tariff_ids: list[str] | None = None

    terms_and_conditions: HttpUrl | None = None

    last_updated: datetime


# =========================================================
# EVSE
# =========================================================


class EVSE(BaseModel):
    uid: str = Field(max_length=36)

    evse_id: str | None = Field(
        default=None,
        max_length=48,
    )

    status: EVSEStatus

    status_schedule: list[StatusSchedule] | None = None

    capabilities: list[Capability] | None = None

    connectors: list[Connector] = Field(
        min_length=1
    )

    floor_level: str | None = Field(
        default=None,
        max_length=4,
    )

    coordinates: GeoLocation | None = None

    physical_reference: str | None = Field(
        default=None,
        max_length=16,
    )

    directions: list[DisplayText] | None = None

    parking_restrictions: list[ParkingRestriction] | None = None

    images: list[Image] | None = None

    last_updated: datetime


# =========================================================
# LOCATION
# =========================================================


class Location(BaseModel):
    country_code: str = Field(
        min_length=2,
        max_length=2,
    )

    party_id: str = Field(
        min_length=3,
        max_length=3,
    )

    id: str = Field(
        max_length=36,
    )

    publish: bool

    publish_allowed_to: list[PublishToken] | None = None

    name: str | None = Field(
        default=None,
        max_length=255,
    )

    address: str = Field(
        max_length=45,
    )

    city: str = Field(
        max_length=45,
    )

    postal_code: str | None = Field(
        default=None,
        max_length=10,
    )

    state: str | None = Field(
        default=None,
        max_length=20,
    )

    country: str = Field(
        min_length=3,
        max_length=3,
    )

    coordinates: GeoLocation

    related_locations: list[AdditionalGeoLocation] | None = None

    parking_type: ParkingType | None = None

    evses: list[EVSE] | None = None

    directions: list[DisplayText] | None = None

    operator: BusinessDetails | None = None

    suboperator: BusinessDetails | None = None

    owner: BusinessDetails | None = None

    facilities: list[Facility] | None = None

    time_zone: str = Field(
        max_length=255,
    )

    opening_times: Hours | None = None

    charging_when_closed: bool = True

    images: list[Image] | None = None

    energy_mix: EnergyMix | None = None

    last_updated: datetime


class EVSEPatch(BaseModel):
    """
    Partial update for an EVSE.

    Only fields supplied in the PATCH request are changed.
    last_updated is mandatory.
    """

    status: EVSEStatus | None = None
    status_schedule: list | None = None
    capabilities: list | None = None
    floor_level: str | None = None
    coordinates: GeoLocation | None = None
    physical_reference: str | None = None
    directions: list | None = None
    parking_restrictions: list | None = None
    images: list | None = None

    last_updated: datetime