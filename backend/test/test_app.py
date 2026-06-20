import asyncio
import importlib
from typing import Any

import pytest
from fastapi.testclient import TestClient


def test_lifespan_starts_and_stops_health_check_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app_module = importlib.import_module("app.app")
    state = {"started": False, "stopped": False}

    async def fake_init_db() -> None:
        return None

    async def fake_close_db() -> None:
        return None

    class FakeHealthCheckWorker:
        def __init__(self, *args: Any) -> None:
            pass

        async def run(self) -> None:
            state["started"] = True
            try:
                await asyncio.Event().wait()
            finally:
                state["stopped"] = True

    monkeypatch.setattr(app_module, "init_db", fake_init_db)
    monkeypatch.setattr(app_module, "close_db", fake_close_db)
    monkeypatch.setattr(app_module, "HealthCheckWorker", FakeHealthCheckWorker)

    with TestClient(app_module.create_app()):
        assert state["started"] is True

    assert state["stopped"] is True
