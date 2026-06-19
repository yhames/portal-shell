from contextlib import asynccontextmanager

import fastapi

from app.database import init_db


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    await init_db()
    yield


def create_app():
    app = fastapi.FastAPI(lifespan=lifespan)
    return app
