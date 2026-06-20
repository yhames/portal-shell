from contextlib import asynccontextmanager

import fastapi

from app.database import init_db
from app.router.registry_router import router as registry_router
from app.router.service_router import router as service_router


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    await init_db()
    yield


def create_app():
    app = fastapi.FastAPI(lifespan=lifespan)
    app.include_router(registry_router)
    app.include_router(service_router)
    return app
