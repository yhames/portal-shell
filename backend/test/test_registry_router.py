import asyncio
from collections.abc import AsyncIterator, Generator
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.app import create_app
from app.router import registry_router


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")

    async def create_tables() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(SQLModel.metadata.create_all)

    asyncio.run(create_tables())

    @asynccontextmanager
    async def test_session() -> AsyncIterator[AsyncSession]:
        async with AsyncSession(engine) as session:
            yield session

    monkeypatch.setattr(registry_router, "get_async_session", test_session)
    yield TestClient(create_app())
    asyncio.run(engine.dispose())


@pytest.fixture
def registration() -> dict[str, object]:
    return {
        "service": "mission-management",
        "name": "Mission Management",
        "description": "Manages missions",
        "version": "1.0.0",
        "icon": "file-lines",
        "order": 10,
        "frontend": {
            "type": "iframe",
            "url": "http://localhost:3001",
        },
        "backend": {
            "url": "http://localhost:8001",
            "health_url": "http://localhost:8001/health",
        },
    }


def test_health_returns_stable_instance_id(client: TestClient) -> None:
    first_response = client.get("/health")
    second_response = client.get("/health")

    assert first_response.status_code == 200
    assert first_response.json()["status"] == "ok"
    assert first_response.json()["instance_id"]
    assert first_response.json()["instance_id"] == second_response.json()["instance_id"]


def test_register_service(
    client: TestClient, registration: dict[str, object]
) -> None:
    response = client.post("/register", json=registration)

    assert response.status_code == 201
    assert response.json() == {"id": 1, **registration}


def test_register_duplicate_service_returns_conflict(
    client: TestClient, registration: dict[str, object]
) -> None:
    assert client.post("/register", json=registration).status_code == 201

    response = client.post("/register", json=registration)

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Service already registered: mission-management"
    }


def test_register_invalid_service_returns_unprocessable_content(
    client: TestClient,
) -> None:
    response = client.post("/register", json={"service": "mission-management"})

    assert response.status_code == 422
