from sqlmodel import SQLModel


class TipoProdottoBase(SQLModel):
    nome: str


class TipoProdottoCreate(TipoProdottoBase):
    pass


class TipoProdottoRead(TipoProdottoBase):
    id: int


class TipoProdottoUpdate(SQLModel):
    nome: str | None = None
