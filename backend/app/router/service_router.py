from fastapi import APIRouter, HTTPException, Response, status
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_async_session
from app.database.model import Service
from app.dto import ServiceResponse, ServiceUpdate

router = APIRouter(prefix="/services", tags=["services"])


async def get_service_or_404(session: AsyncSession, service_name: str) -> Service:
    result = await session.exec(select(Service).where(Service.service == service_name))
    service = result.first()
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service not found: {service_name}",
        )
    return service


@router.get("", response_model=list[ServiceResponse])
async def list_services() -> list[ServiceResponse]:
    async with get_async_session() as session:
        result = await session.exec(
            select(Service).order_by(col(Service.order), col(Service.name))
        )
        return [ServiceResponse.model_validate(service) for service in result.all()]


@router.get("/{service_name}", response_model=ServiceResponse)
async def get_service(service_name: str) -> ServiceResponse:
    async with get_async_session() as session:
        service = await get_service_or_404(session, service_name)
        return ServiceResponse.model_validate(service)


@router.post("/{service_name}/update", response_model=ServiceResponse)
async def update_service(
    service_name: str, update: ServiceUpdate
) -> ServiceResponse:
    async with get_async_session() as session:
        service = await get_service_or_404(session, service_name)
        update_data = update.model_dump(exclude_unset=True, exclude_none=True)

        for field, value in update_data.items():
            setattr(service, field, value)

        session.add(service)
        await session.commit()
        await session.refresh(service)
        return ServiceResponse.model_validate(service)


@router.post(
    "/{service_name}/delete",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_service(service_name: str) -> Response:
    async with get_async_session() as session:
        service = await get_service_or_404(session, service_name)
        await session.delete(service)
        await session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
