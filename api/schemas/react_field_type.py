from sqlmodel import SQLModel


class ReactFieldTypeBase(SQLModel):
    nome: str


class ReactFieldTypeCreate(ReactFieldTypeBase):
    pass


class ReactFieldTypeRead(ReactFieldTypeBase):
    id: int


class ReactFieldTypeUpdate(SQLModel):
    nome: str | None = None
