from enum import Enum

from pydantic import BaseModel, HttpUrl


class InterfaceRole(str, Enum):
    SENDER = "SENDER"
    RECEIVER = "RECEIVER"


class ModuleID(str, Enum):
    CREDENTIALS = "credentials"
    LOCATIONS = "locations"
    SESSIONS = "sessions"
    CDRS = "cdrs"
    TARIFFS = "tariffs"
    TOKENS = "tokens"
    COMMANDS = "commands"
    CHARGING_PROFILES = "chargingprofiles"
    HUB_CLIENT_INFO = "hubclientinfo"


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