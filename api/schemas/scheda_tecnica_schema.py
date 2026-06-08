from sqlmodel import SQLModel


class SchedaTecnicaSchemaBase(SQLModel):
    fornitore_id: int
    tipo_prodotto_id: int
    prodotto_nome: str | None = None


class SchedaTecnicaSchemaCreate(SchedaTecnicaSchemaBase):
    pass


class SchedaTecnicaSchemaRead(SchedaTecnicaSchemaBase):
    id: int


class SchedaTecnicaSchemaUpdate(SQLModel):
    fornitore_id: int | None = None
    tipo_prodotto_id: int | None = None
    prodotto_nome: str | None = None
