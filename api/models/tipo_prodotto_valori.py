from sqlmodel import SQLModel, Field


class TipoProdottoValori(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nome: str  # "Materiale", "Campo", etc.
