import asyncio
import logging
import random
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx2
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config.settings import Settings
from app.database.model import ServiceRecord
from app.dto import BackendConfig, HealthState

logger = logging.getLogger("service_registry.health_check")


@dataclass(frozen=True)
class HealthCheckTarget:
    service_id: int
    health_url: str


@dataclass(frozen=True)
class HealthCheckResult:
    service_id: int
    health_url: str
    healthy: bool
    checked_at: datetime
    error: str | None = None


class HealthCheckWorker:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        settings: Settings,
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings
        self._task: asyncio.Task | None = None
        self._running = False

    async def check_once(self, client: httpx2.AsyncClient) -> None:
        targets = await self._load_targets()
        semaphore = asyncio.Semaphore(
            self._settings.health_check_max_concurrency
        )
        results = await asyncio.gather(
            *(self._check_target(client, target, semaphore) for target in targets)
        )
        await self._apply_results(results)

    def start(self) -> None:
        """외부에서 워커를 시작하는 메서드"""
        if self._task is not None and not self._task.done():
            # 이미 실행 중이면 중복 실행 방지
            return

        self._running = True
        # 클래스 내부에서 직접 태스크를 생성하고 관리
        self._task = asyncio.create_task(self.run())

    async def stop(self) -> None:
        """외부에서 워커를 안전하게 종료하는 메서드 (비동기)"""
        if self._task is None or self._task.done():
            return

        self._running = False
        self._task.cancel()  # 실행 중인 태스크 취소

        try:
            await self._task  # 태스크가 완전히 종료될 때까지 대기
        except asyncio.CancelledError:
            pass  # 취소로 인한 예외는 정상적이므로 무시
        finally:
            self._task = None

    async def run(self) -> None:
        async with httpx2.AsyncClient(follow_redirects=False) as client:
            while True:
                try:
                    await self.check_once(client)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("Health check cycle failed")

                jitter = random.uniform(
                    1 - self._settings.health_check_jitter_ratio,
                    1 + self._settings.health_check_jitter_ratio,
                )
                await asyncio.sleep(
                    self._settings.health_check_interval_seconds * jitter
                )

    async def _load_targets(self) -> list[HealthCheckTarget]:
        async with self._session_factory() as session:
            records = (await session.exec(select(ServiceRecord))).all()
            return [
                HealthCheckTarget(
                    service_id=record.id,
                    health_url=str(
                        BackendConfig.model_validate(record.backend).health_url
                    ),
                )
                for record in records
                if record.id is not None
            ]

    async def _check_target(
        self,
        client: httpx2.AsyncClient,
        target: HealthCheckTarget,
        semaphore: asyncio.Semaphore,
    ) -> HealthCheckResult:
        async with semaphore:
            try:
                response = await client.get(
                    target.health_url,
                    timeout=self._settings.health_check_timeout_seconds,
                )
                healthy = response.is_success
                error = None if healthy else f"HTTP {response.status_code}"
            except httpx2.RequestError as exc:
                healthy = False
                error = str(exc)[:500]

        return HealthCheckResult(
            service_id=target.service_id,
            health_url=target.health_url,
            healthy=healthy,
            checked_at=datetime.now(UTC),
            error=error,
        )

    async def _apply_results(self, results: list[HealthCheckResult]) -> None:
        async with self._session_factory() as session:
            for result in results:
                record = await session.get(ServiceRecord, result.service_id)
                if record is None:
                    continue
                current_url = str(
                    BackendConfig.model_validate(record.backend).health_url
                )
                if current_url != result.health_url:
                    continue

                record.health_checked_at = result.checked_at
                if result.healthy:
                    record.health_state = HealthState.HEALTHY
                    record.last_healthy_at = result.checked_at
                    record.consecutive_failures = 0
                    record.health_error = None
                else:
                    record.consecutive_failures += 1
                    if (
                        record.consecutive_failures
                        >= self._settings.health_check_failure_threshold
                    ):
                        record.health_state = HealthState.UNHEALTHY
                    record.health_error = result.error
                session.add(record)

            await session.commit()
