from datetime import datetime
from enum import StrEnum

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class FrontendConfig(BaseModel):
    type: str
    url: str


class BackendConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    health_url: AnyHttpUrl = Field(alias="healthUrl")


class DisplayConfig(BaseModel):
    name: str
    icon: str
    order: int = 10


class ServiceMetadata(BaseModel):
    namespace: str
    name: str
    version: str


class ServiceSpec(BaseModel):
    description: str
    display: DisplayConfig
    frontend: FrontendConfig
    backend: BackendConfig


class ServiceRegistration(BaseModel):
    metadata: ServiceMetadata
    spec: ServiceSpec


class HealthState(StrEnum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class ServiceHealthStatus(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    state: HealthState
    checked_at: datetime | None = Field(alias="checkedAt")
    last_healthy_at: datetime | None = Field(alias="lastHealthyAt")
    consecutive_failures: int = Field(alias="consecutiveFailures")
    error: str | None


class ServiceStatus(BaseModel):
    health: ServiceHealthStatus


class ServiceResponse(ServiceRegistration):
    id: int
    status: ServiceStatus


class DisplayUpdate(BaseModel):
    name: str | None = None
    icon: str | None = None
    order: int | None = None


class ServiceMetadataUpdate(BaseModel):
    version: str | None = None


class ServiceSpecUpdate(BaseModel):
    description: str | None = None
    display: DisplayUpdate | None = None
    frontend: FrontendConfig | None = None
    backend: BackendConfig | None = None


class ServiceUpdate(BaseModel):
    metadata: ServiceMetadataUpdate | None = None
    spec: ServiceSpecUpdate | None = None
