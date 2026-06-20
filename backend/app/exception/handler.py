from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from .errors import (
    ServiceAlreadyExistsError,
    ServiceNotFoundError,
    ServiceRecordNotPersistedError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ServiceNotFoundError)
    async def handle_service_not_found(
        request: Request, exc: ServiceNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"code": exc.code, "detail": exc.detail},
        )

    @app.exception_handler(ServiceAlreadyExistsError)
    async def handle_service_already_exists(
        request: Request, exc: ServiceAlreadyExistsError
    ) -> JSONResponse:
        return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"code": exc.code, "detail": exc.detail},
        )

    @app.exception_handler(ServiceRecordNotPersistedError)
    async def handle_service_record_not_persisted(
        request: Request, exc: ServiceRecordNotPersistedError
    ) -> JSONResponse:
        return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": exc.code, "detail": exc.detail},
        )
