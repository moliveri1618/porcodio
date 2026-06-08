from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class SchedaTecnicaPezzo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    progetto_id: int = Field(foreign_key="progetti.id")
    fornitore_id: int = Field(foreign_key="fornitore.id")
    tipo_prodotto_id: int = Field(foreign_key="tipo_prodotto.id")

    prodotto_nome: str | None = None
    prodotto_val: str | None = None
