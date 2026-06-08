from sqlmodel import SQLModel


class SchedaTecnicaPezzoBase(SQLModel):
    progetto_id: int
    fornitore_id: int
    tipo_prodotto_id: int
    prodotto_nome: str | None = None
    prodotto_val: str | None = None


class SchedaTecnicaPezzoCreate(SchedaTecnicaPezzoBase):
    pass


class SchedaTecnicaPezzoRead(SchedaTecnicaPezzoBase):
    id: int


class SchedaTecnicaPezzoUpdate(SQLModel):
    progetto_id: int | None = None
    fornitore_id: int | None = None
    tipo_prodotto_id: int | None = None
    prodotto_nome: str | None = None
    prodotto_val: str | None = None
