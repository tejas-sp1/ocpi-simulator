from enum import Enum
from pydantic import BaseModel, HttpUrl


class InterfaceRole(str, Enum):
    SENDER = "SENDER"
    RECEIVER = "RECEIVER"


class ModuleID(str, Enum):
    CDRS = "cdrs"
    CHARGING_PROFILES = "chargingprofiles"
    COMMANDS = "commands"
    CREDENTIALS = "credentials"
    HUBCLIENTINFO = "hubclientinfo"
    LOCATIONS = "locations"
    SESSIONS = "sessions"
    TARIFFS = "tariffs"
    TOKENS = "tokens"


class Version(BaseModel):
    version: str
    url: HttpUrl


class Endpoint(BaseModel):
    identifier: ModuleID
    role: InterfaceRole
    url: HttpUrl


class VersionDetails(BaseModel):
    version: str
    endpoints: list[Endpoint]