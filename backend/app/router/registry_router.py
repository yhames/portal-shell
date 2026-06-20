from uuid import uuid4

from fastapi import APIRouter, Response, status

from app.database import get_async_session
from app.database.model import ServiceRecord
from app.dto import (
    BackendConfig,
    DisplayConfig,
    FrontendConfig,
    HealthResponse,
    ServiceMetadata,
    ServiceRegistration,
    ServiceResponse,
    ServiceSpec,
    ServiceUpdate,
)
from app.exception import ServiceRecordNotPersistedError
from app.service import (
    delete_service_record,
    get_service_record,
    list_service_records,
    register_service_record,
    update_service_record,
)

router = APIRouter()
INSTANCE_ID = str(uuid4())


def _to_service_response(service: ServiceRecord) -> ServiceResponse:
    if service.id is None:
        raise ServiceRecordNotPersistedError()

    return ServiceResponse(
        id=service.id,
        metadata=ServiceMetadata(
            namespace=service.namespace,
            name=service.name,
            version=service.version,
        ),
        spec=ServiceSpec(
            description=service.description,
            display=DisplayConfig(
                name=service.display_name,
                icon=service.display_icon,
                order=service.display_order,
            ),
            frontend=FrontendConfig.model_validate(service.frontend),
            backend=BackendConfig.model_validate(service.backend),
        ),
    )


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", instance_id=INSTANCE_ID)


@router.post(
    "/register",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_service(registration: ServiceRegistration) -> ServiceResponse:
    async with get_async_session() as session:
        service = await register_service_record(session, registration)
        return _to_service_response(service)


@router.get("/services", response_model=list[ServiceResponse])
async def list_services() -> list[ServiceResponse]:
    async with get_async_session() as session:
        services = await list_service_records(session)
        return [_to_service_response(service) for service in services]


@router.get("/services/{namespace}/{name}", response_model=ServiceResponse)
async def get_service(namespace: str, name: str) -> ServiceResponse:
    async with get_async_session() as session:
        service = await get_service_record(session, namespace, name)
        return _to_service_response(service)


@router.post(
    "/services/{namespace}/{name}/update",
    response_model=ServiceResponse,
)
async def update_service(
    namespace: str, name: str, update: ServiceUpdate
) -> ServiceResponse:
    async with get_async_session() as session:
        service = await update_service_record(session, namespace, name, update)
        return _to_service_response(service)


@router.post(
    "/services/{namespace}/{name}/delete",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_service(namespace: str, name: str) -> Response:
    async with get_async_session() as session:
        await delete_service_record(session, namespace, name)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
