import asyncio
from collections.abc import AsyncIterator, Generator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.app import create_app
from app.router import registry_router


@pytest.fixture
def session_factory(
    tmp_path: Path,
) -> Generator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def create_tables() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(SQLModel.metadata.create_all)

    asyncio.run(create_tables())
    yield factory
    asyncio.run(engine.dispose())


@pytest.fixture
def client(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:

    @asynccontextmanager
    async def test_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    monkeypatch.setattr(registry_router, "get_async_session", test_session)
    return TestClient(create_app())


@pytest.fixture
def registration() -> dict[str, Any]:
    return {
        "metadata": {
            "namespace": "robotics",
            "name": "mission-management",
            "version": "1.0.0",
        },
        "spec": {
            "description": "Manages missions",
            "display": {
                "name": "Mission Management",
                "icon": "file-lines",
                "order": 10,
            },
            "frontend": {
                "type": "iframe",
                "url": "http://localhost:3001",
            },
            "backend": {
                "healthUrl": "http://localhost:8001/health",
            },
        },
    }
