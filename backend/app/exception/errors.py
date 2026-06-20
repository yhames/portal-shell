from enum import StrEnum


class ErrorCode(StrEnum):
    SERVICE_ALREADY_EXISTS = "REG-1001"
    SERVICE_NOT_FOUND = "REG-2001"
    SERVICE_RECORD_NOT_PERSISTED = "REG-9001"


class RegistryError(Exception):
    def __init__(self, code: ErrorCode, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(detail)


class ServiceNotFoundError(RegistryError):
    def __init__(self, namespace: str, name: str) -> None:
        super().__init__(
            ErrorCode.SERVICE_NOT_FOUND,
            f"Service not found: {namespace}/{name}",
        )


class ServiceAlreadyExistsError(RegistryError):
    def __init__(self, namespace: str, name: str) -> None:
        super().__init__(
            ErrorCode.SERVICE_ALREADY_EXISTS,
            f"Service already registered: {namespace}/{name}",
        )


class ServiceRecordNotPersistedError(RegistryError):
    def __init__(self) -> None:
        super().__init__(
            ErrorCode.SERVICE_RECORD_NOT_PERSISTED,
            "Service record must be persisted before serialization",
        )
