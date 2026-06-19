from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class FrontendConfig(SQLModel):
    type: str
    url: str


class BackendConfig(SQLModel):
    url: str
    health_url: str


class ServiceRegistration(SQLModel):
    service: str
    name: str
    description: str
    version: str
    icon: str
    order: int = 10
    frontend: FrontendConfig
    backend: BackendConfig


class Service(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    service: str = Field(index=True, unique=True)
    name: str
    description: str
    version: str
    icon: str
    order: int = 10
    frontend: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    backend: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))


class ServiceResponse(ServiceRegistration):
    id: int


class HealthResponse(SQLModel):
    status: str
    instance_id: str
