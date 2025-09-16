from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String


class Prodotto(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nome_prodotto: str = Field(
        sa_column=Column(String(255), unique=True, nullable=False, index=True)
    )