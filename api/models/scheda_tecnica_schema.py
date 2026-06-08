from sqlmodel import SQLModel, Field


class SchedaTecnicaSchema(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    fornitore_id: int = Field(foreign_key="fornitore.id")
    tipo_prodotto_id: int = Field(foreign_key="tipo_prodotto.id")
    
    prodotto_nome: str | None = None
