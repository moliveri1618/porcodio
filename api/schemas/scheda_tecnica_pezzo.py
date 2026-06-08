from sqlmodel import SQLModel


class SchedaTecnicaPezzoBase(SQLModel):
    progetto_id: int
    scheda_tecnica_schema_id: int
    valore: str | None = None


class SchedaTecnicaPezzoCreate(SchedaTecnicaPezzoBase):
    pass


class SchedaTecnicaPezzoRead(SchedaTecnicaPezzoBase):
    id: int


class SchedaTecnicaPezzoUpdate(SQLModel):
    progetto_id: int | None = None
    scheda_tecnica_schema_id: int | None = None
    valore: str | None = None
