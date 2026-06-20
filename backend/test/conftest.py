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
