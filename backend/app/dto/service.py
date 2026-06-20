from pydantic import BaseModel, ConfigDict


class FrontendConfig(BaseModel):
    type: str
    url: str


class BackendConfig(BaseModel):
    url: str
    health_url: str


class ServiceRegistration(BaseModel):
    service: str
    name: str
    description: str
    version: str
    icon: str
    order: int = 10
    frontend: FrontendConfig
    backend: BackendConfig


class ServiceResponse(ServiceRegistration):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ServiceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    version: str | None = None
    icon: str | None = None
    order: int | None = None
    frontend: FrontendConfig | None = None
    backend: BackendConfig | None = None
