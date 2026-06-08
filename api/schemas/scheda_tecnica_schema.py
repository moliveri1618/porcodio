from sqlmodel import SQLModel
from typing import List


class SchedaTecnicaSchemaBase(SQLModel):
    fornitore_id: int
    tipo_prodotto_id: int
    tipo_prodotto_valori_id: int
    field_type_id: int 
    tipo_prodotto_dropdown_id: List[int] = []


class SchedaTecnicaSchemaCreate(SchedaTecnicaSchemaBase):
    pass


class SchedaTecnicaSchemaRead(SchedaTecnicaSchemaBase):
    id: int


class SchedaTecnicaSchemaUpdate(SQLModel):
    fornitore_id: int | None = None
    tipo_prodotto_id: int | None = None
    tipo_prodotto_valori_id: int | None = None
    field_type_id: int 
    tipo_prodotto_dropdown_id: List[int] | None = None
