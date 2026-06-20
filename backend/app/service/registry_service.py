from sqlalchemy.exc import IntegrityError
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database.model import ServiceRecord
from app.dto import ServiceRegistration, ServiceUpdate
from app.exception import ServiceAlreadyExistsError, ServiceNotFoundError


async def list_service_records(session: AsyncSession) -> list[ServiceRecord]:
    result = await session.exec(
        select(ServiceRecord).order_by(
            col(ServiceRecord.display_order), col(ServiceRecord.display_name)
        )
    )
    return list(result.all())


async def get_service_record(
    session: AsyncSession, namespace: str, name: str
) -> ServiceRecord:
    result = await session.exec(
        select(ServiceRecord).where(
            ServiceRecord.namespace == namespace,
            ServiceRecord.name == name,
        )
    )
    service = result.first()
    if service is None:
        raise ServiceNotFoundError(namespace, name)
    return service


async def register_service_record(
    session: AsyncSession, registration: ServiceRegistration
) -> ServiceRecord:
    result = await session.exec(
        select(ServiceRecord).where(
            ServiceRecord.namespace == registration.metadata.namespace,
            ServiceRecord.name == registration.metadata.name,
        )
    )
    if result.first() is not None:
        raise ServiceAlreadyExistsError(
            registration.metadata.namespace,
            registration.metadata.name,
        )

    service = ServiceRecord(
        namespace=registration.metadata.namespace,
        name=registration.metadata.name,
        display_name=registration.spec.display.name,
        display_icon=registration.spec.display.icon,
        description=registration.spec.description,
        version=registration.metadata.version,
        display_order=registration.spec.display.order,
        frontend=registration.spec.frontend.model_dump(mode="json"),
        backend=registration.spec.backend.model_dump(mode="json", by_alias=True),
    )
    session.add(service)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ServiceAlreadyExistsError(
            registration.metadata.namespace,
            registration.metadata.name,
        ) from exc

    await session.refresh(service)
    return service


async def update_service_record(
    session: AsyncSession,
    namespace: str,
    name: str,
    update: ServiceUpdate,
) -> ServiceRecord:
    service = await get_service_record(session, namespace, name)
    if update.metadata is not None and update.metadata.version is not None:
        service.version = update.metadata.version

    if update.spec is not None:
        spec = update.spec
        if spec.description is not None:
            service.description = spec.description
        if spec.frontend is not None:
            service.frontend = spec.frontend.model_dump(mode="json")
        if spec.backend is not None:
            service.backend = spec.backend.model_dump(mode="json", by_alias=True)
        if spec.display is not None:
            if spec.display.name is not None:
                service.display_name = spec.display.name
            if spec.display.icon is not None:
                service.display_icon = spec.display.icon
            if spec.display.order is not None:
                service.display_order = spec.display.order

    session.add(service)
    await session.commit()
    await session.refresh(service)
    return service


async def delete_service_record(
    session: AsyncSession, namespace: str, name: str
) -> None:
    service = await get_service_record(session, namespace, name)
    await session.delete(service)
    await session.commit()
