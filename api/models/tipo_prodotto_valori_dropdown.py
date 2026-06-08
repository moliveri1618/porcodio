from sqlmodel import SQLModel, Field


class TipoProdottoValoriDropdown(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nome: str  # "PVC", "Alluminio", etc.
