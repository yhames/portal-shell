import asyncio
from typing import Any

import httpx2
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config.settings import Settings
from app.database.model import ServiceRecord
from app.dto import ServiceRegistration, ServiceUpdate
from app.service import register_service_record, update_service_record
from app.worker import HealthCheckWorker


def _create_worker(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    failure_threshold: int = 3,
) -> HealthCheckWorker:
    return HealthCheckWorker(
        session_factory,
        Settings(
            health_check_timeout_seconds=1,
            health_check_failure_threshold=failure_threshold,
            health_check_max_concurrency=1,
        ),
    )


async def _register_service(
    session_factory: async_sessionmaker[AsyncSession],
    registration: dict[str, Any],
) -> None:
    async with session_factory() as session:
        await register_service_record(
            session,
            ServiceRegistration.model_validate(registration),
        )


async def _get_service(
    session_factory: async_sessionmaker[AsyncSession],
) -> ServiceRecord:
    async with session_factory() as session:
        service = (await session.exec(select(ServiceRecord))).one()
        return service


def test_health_check_marks_service_healthy(
    session_factory: async_sessionmaker[AsyncSession],
    registration: dict[str, Any],
) -> None:
    async def verify() -> None:
        await _register_service(session_factory, registration)
        transport = httpx2.MockTransport(lambda request: httpx2.Response(200))
        worker = _create_worker(session_factory)

        async with httpx2.AsyncClient(transport=transport) as client:
            await worker.check_once(client)

        service = await _get_service(session_factory)
        assert service.health_state == "healthy"
        assert service.health_checked_at is not None
        assert service.last_healthy_at == service.health_checked_at
        assert service.consecutive_failures == 0
        assert service.health_error is None

    asyncio.run(verify())


def test_health_check_failure_threshold_and_recovery(
    session_factory: async_sessionmaker[AsyncSession],
    registration: dict[str, Any],
) -> None:
    async def verify() -> None:
        await _register_service(session_factory, registration)
        status_codes = iter([500, 503, 204])
        transport = httpx2.MockTransport(
            lambda request: httpx2.Response(next(status_codes))
        )
        worker = _create_worker(session_factory, failure_threshold=2)

        async with httpx2.AsyncClient(transport=transport) as client:
            await worker.check_once(client)
            first_failure = await _get_service(session_factory)
            assert first_failure.health_state == "unknown"
            assert first_failure.consecutive_failures == 1
            assert first_failure.health_error == "HTTP 500"

            await worker.check_once(client)
            unhealthy = await _get_service(session_factory)
            assert unhealthy.health_state == "unhealthy"
            assert unhealthy.consecutive_failures == 2
            assert unhealthy.health_error == "HTTP 503"

            await worker.check_once(client)

        recovered = await _get_service(session_factory)
        assert recovered.health_state == "healthy"
        assert recovered.consecutive_failures == 0
        assert recovered.health_error is None

    asyncio.run(verify())


def test_health_url_update_resets_health_status(
    session_factory: async_sessionmaker[AsyncSession],
    registration: dict[str, Any],
) -> None:
    async def verify() -> None:
        await _register_service(session_factory, registration)
        transport = httpx2.MockTransport(lambda request: httpx2.Response(500))
        worker = _create_worker(session_factory, failure_threshold=1)

        async with httpx2.AsyncClient(transport=transport) as client:
            await worker.check_once(client)

        async with session_factory() as session:
            await update_service_record(
                session,
                "robotics",
                "mission-management",
                ServiceUpdate.model_validate(
                    {
                        "spec": {
                            "backend": {
                                "healthUrl": "http://localhost:8002/health"
                            }
                        }
                    }
                ),
            )

        service = await _get_service(session_factory)
        assert service.health_state == "unknown"
        assert service.health_checked_at is None
        assert service.last_healthy_at is None
        assert service.consecutive_failures == 0
        assert service.health_error is None

    asyncio.run(verify())


def test_health_status_is_exposed_by_service_api(
    client: TestClient,
    session_factory: async_sessionmaker[AsyncSession],
    registration: dict[str, Any],
) -> None:
    assert client.post("/register", json=registration).status_code == 201

    async def check_health() -> None:
        transport = httpx2.MockTransport(lambda request: httpx2.Response(200))
        worker = _create_worker(session_factory)
        async with httpx2.AsyncClient(transport=transport) as http_client:
            await worker.check_once(http_client)

    asyncio.run(check_health())
    response = client.get("/services/robotics/mission-management")

    assert response.status_code == 200
    health = response.json()["status"]["health"]
    assert health["state"] == "healthy"
    assert health["checkedAt"] is not None
    assert health["lastHealthyAt"] == health["checkedAt"]
    assert health["consecutiveFailures"] == 0
    assert health["error"] is None
