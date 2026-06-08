from sqlmodel import SQLModel, Field


class ReactFieldType(SQLModel, table=True):

    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(index=True, unique=True)
