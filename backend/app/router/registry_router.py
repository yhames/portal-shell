from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database import get_async_session
from app.database.model import (
    HealthResponse,
    Service,
    ServiceRegistration,
    ServiceResponse,
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
        existing_service = await session.exec(
            select(Service).where(Service.service == registration.service)
        )
        if existing_service.first() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Service already registered: {registration.service}",
            )

        service_data = registration.model_dump(exclude={"frontend", "backend"})
        service = Service(
            **service_data,
            frontend=registration.frontend.model_dump(mode="json"),
            backend=registration.backend.model_dump(mode="json"),
        )
        session.add(service)

        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Service already registered: {registration.service}",
            ) from exc

        await session.refresh(service)
        return ServiceResponse.model_validate(service)
