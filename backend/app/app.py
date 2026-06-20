import asyncio
from contextlib import asynccontextmanager, suppress

import fastapi

from app.config import get_settings
from app.database import async_session_maker, close_db, init_db
from app.exception import register_exception_handlers
from app.router.registry_router import router as registry_router
from app.worker import HealthCheckWorker


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    await init_db()
    health_check_worker = HealthCheckWorker(async_session_maker, get_settings())
    health_check_worker.start()

    yield

    await health_check_worker.stop()
    await close_db()


def create_app():
    app = fastapi.FastAPI(lifespan=lifespan)
    register_exception_handlers(app)
    app.include_router(registry_router)
    return app
