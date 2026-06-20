from sqlalchemy.exc import IntegrityError
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database.model import ServiceRecord
from app.dto import ServiceRegistration, ServiceUpdate


class ServiceNotFoundError(Exception):
    pass


class ServiceAlreadyExistsError(Exception):
    pass


async def list_service_records(session: AsyncSession) -> list[ServiceRecord]:
    result = await session.exec(
        select(ServiceRecord).order_by(
            col(ServiceRecord.order), col(ServiceRecord.name)
        )
    )
    return list(result.all())


async def get_service_record(session: AsyncSession, service_name: str) -> ServiceRecord:
    result = await session.exec(
        select(ServiceRecord).where(ServiceRecord.service == service_name)
    )
    service = result.first()
    if service is None:
        raise ServiceNotFoundError(service_name)
    return service


async def register_service_record(
    session: AsyncSession, registration: ServiceRegistration
) -> ServiceRecord:
    result = await session.exec(
        select(ServiceRecord).where(ServiceRecord.service == registration.service)
    )
    if result.first() is not None:
        raise ServiceAlreadyExistsError(registration.service)

    service_data = registration.model_dump(exclude={"frontend", "backend"})
    service = ServiceRecord(
        **service_data,
        frontend=registration.frontend.model_dump(mode="json"),
        backend=registration.backend.model_dump(mode="json"),
    )
    session.add(service)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ServiceAlreadyExistsError(registration.service) from exc

    await session.refresh(service)
    return service


async def update_service_record(
    session: AsyncSession, service_name: str, update: ServiceUpdate
) -> ServiceRecord:
    service = await get_service_record(session, service_name)
    update_data = update.model_dump(exclude_unset=True, exclude_none=True)

    for field, value in update_data.items():
        setattr(service, field, value)

    session.add(service)
    await session.commit()
    await session.refresh(service)
    return service


async def delete_service_record(session: AsyncSession, service_name: str) -> None:
    service = await get_service_record(session, service_name)
    await session.delete(service)
    await session.commit()
