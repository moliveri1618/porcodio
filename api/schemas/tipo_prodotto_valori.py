from sqlmodel import SQLModel


class TipoProdottoValoriBase(SQLModel):
    nome: str


class TipoProdottoValoriCreate(TipoProdottoValoriBase):
    pass


class TipoProdottoValoriRead(TipoProdottoValoriBase):
    id: int


class TipoProdottoValoriUpdate(SQLModel):
    nome: str | None = None
