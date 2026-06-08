from sqlmodel import SQLModel


class SchedaTecnicaSchemaBase(SQLModel):
    fornitore_id: int
    tipo_prodotto_id: int
    nome: str
    options: list[str] | None = None


class SchedaTecnicaSchemaCreate(SchedaTecnicaSchemaBase):
    pass


class SchedaTecnicaSchemaRead(SchedaTecnicaSchemaBase):
    id: int


class SchedaTecnicaSchemaUpdate(SQLModel):
    fornitore_id: int | None = None
    tipo_prodotto_id: int | None = None
    nome: str | None = None
    options: list[str] | None = None
