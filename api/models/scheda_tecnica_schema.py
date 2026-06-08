from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


class SchedaTecnicaSchema(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    fornitore_id: int = Field(foreign_key="fornitore.id")
    tipo_prodotto_id: int = Field(foreign_key="tipoprodotto.id")

    nome: str

    options: list[str] | None = Field(default=None, sa_column=Column(JSONB))
