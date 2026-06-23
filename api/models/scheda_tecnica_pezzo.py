from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class SchedaTecnicaPezzo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    progetto_id: int = Field(
        foreign_key="progetti.id", 
        index=True
    )
    scheda_tecnica_schema_id: int = Field(
        foreign_key="schedatecnicaschema.id", index=True
    )
    riferimento: str = Field(index=True)  # "1", "2", "3", etc.

    valore: str
