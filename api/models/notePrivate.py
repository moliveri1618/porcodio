from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text


class NotePrivate(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(..., nullable=False)
    note: str = Field(sa_column=Column(Text, nullable=False))
