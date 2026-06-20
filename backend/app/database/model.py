from typing import Any, ClassVar

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel


class ServiceRecord(SQLModel, table=True):
    __tablename__: ClassVar[str] = "services"  # pyright: ignore[reportAssignmentType]
    __table_args__: ClassVar[tuple[UniqueConstraint]] = (
        UniqueConstraint(
            "namespace",
            "name",
            name="uq_services_namespace_name",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    namespace: str = Field(index=True)
    name: str = Field(index=True)
    display_name: str
    display_icon: str
    description: str
    version: str
    display_order: int = 10
    frontend: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    backend: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
