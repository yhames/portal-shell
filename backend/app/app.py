from contextlib import asynccontextmanager

import fastapi

from app.database import init_db
from app.exception import register_exception_handlers
from app.router.registry_router import router as registry_router


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    await init_db()
    yield


def create_app():
    app = fastapi.FastAPI(lifespan=lifespan)
    register_exception_handlers(app)
    app.include_router(registry_router)
    return app
