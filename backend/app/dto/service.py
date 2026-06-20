from pydantic import BaseModel, ConfigDict, Field


class FrontendConfig(BaseModel):
    type: str
    url: str


class BackendConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    health_url: str = Field(alias="healthUrl")


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


class ServiceResponse(ServiceRegistration):
    id: int


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
