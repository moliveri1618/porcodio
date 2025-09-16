# schemas/prodotto.py
from pydantic import BaseModel
from typing import Optional


class ProdottoBase(BaseModel):
    nome_prodotto: str


class ProdottoCreate(ProdottoBase):
    pass


class ProdottoRead(ProdottoBase):
    id: int


class ProdottoUpdate(BaseModel):
    nome_prodotto: Optional[str] = None
