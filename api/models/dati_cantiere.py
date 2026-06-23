from typing import Optional
from sqlmodel import SQLModel, Field


class CantiereExtractor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    progetto_id: Optional[int] = Field(
        default=None,
        foreign_key="progetti.id",
        index=True,
    )

    campo: Optional[str] = Field(
        default=None,
        nullable=True,
        index=True,
    )

    valore: Optional[str] = Field(
        default=None,
        nullable=True,
    )
