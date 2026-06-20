from typing import Any, ClassVar

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class ServiceRecord(SQLModel, table=True):
    __tablename__: ClassVar[str] = "services"  # pyright: ignore[reportAssignmentType]

    id: int | None = Field(default=None, primary_key=True)
    service: str = Field(index=True, unique=True)
    name: str
    description: str
    version: str
    icon: str
    order: int = 10
    frontend: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    backend: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
