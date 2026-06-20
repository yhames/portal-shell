from uuid import uuid4

from fastapi import APIRouter, HTTPException, Response, status

from app.database import get_async_session
from app.dto import (
    HealthResponse,
    ServiceRegistration,
    ServiceResponse,
    ServiceUpdate,
)
from app.service import (
    ServiceAlreadyExistsError,
    ServiceNotFoundError,
    delete_service_record,
    get_service_record,
    list_service_records,
    register_service_record,
    update_service_record,
)

router = APIRouter()
INSTANCE_ID = str(uuid4())


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
        try:
            service = await register_service_record(session, registration)
        except ServiceAlreadyExistsError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Service already registered: {registration.service}",
            ) from exc

        return ServiceResponse.model_validate(service)


@router.get("/services", response_model=list[ServiceResponse])
async def list_services() -> list[ServiceResponse]:
    async with get_async_session() as session:
        services = await list_service_records(session)
        return [ServiceResponse.model_validate(service) for service in services]


@router.get("/services/{service_name}", response_model=ServiceResponse)
async def get_service(service_name: str) -> ServiceResponse:
    async with get_async_session() as session:
        try:
            service = await get_service_record(session, service_name)
        except ServiceNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service not found: {service_name}",
            ) from exc
        return ServiceResponse.model_validate(service)


@router.post("/services/{service_name}/update", response_model=ServiceResponse)
async def update_service(
    service_name: str, update: ServiceUpdate
) -> ServiceResponse:
    async with get_async_session() as session:
        try:
            service = await update_service_record(session, service_name, update)
        except ServiceNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service not found: {service_name}",
            ) from exc
        return ServiceResponse.model_validate(service)


@router.post(
    "/services/{service_name}/delete",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_service(service_name: str) -> Response:
    async with get_async_session() as session:
        try:
            await delete_service_record(session, service_name)
        except ServiceNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service not found: {service_name}",
            ) from exc
        return Response(status_code=status.HTTP_204_NO_CONTENT)
