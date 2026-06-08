from sqlmodel import SQLModel


class TipoProdottoValoriDropDownBase(SQLModel):
    nome: str


class TipoProdottoValoriDropDownCreate(TipoProdottoValoriDropDownBase):
    pass


class TipoProdottoValoriDropDownRead(TipoProdottoValoriDropDownBase):
    id: int


class TipoProdottoValoriDropDownUpdate(SQLModel):
    nome: str | None = None
