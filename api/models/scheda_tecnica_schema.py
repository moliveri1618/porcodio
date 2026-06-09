from sqlmodel import Integer, SQLModel, Field, Column
from typing import List
from sqlalchemy.dialects.postgresql import ARRAY



class SchedaTecnicaSchema(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    fornitore_id: int = Field(
        foreign_key="fornitore.id",
        index=True,
    )
    tipo_prodotto_id: int = Field(
        foreign_key="tipoprodotto.id", 
        index=True
    )
    tipo_prodotto_valori_id: int = Field(
        foreign_key="tipoprodottovalori.id", index=True
    )
    field_type_id: int = Field(
        foreign_key="reactfieldtype.id",
        index=True,
    )
    tipo_prodotto_dropdown_id: List[int] = Field(
        default_factory=list, sa_column=Column(ARRAY(Integer))
    )
