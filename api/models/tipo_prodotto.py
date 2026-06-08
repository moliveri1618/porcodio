from sqlmodel import SQLModel, Field


class TipoProdotto(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nome: str  # "avvolgibile", "finestra", etc.
