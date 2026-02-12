# schemas/note_private.py
from pydantic import BaseModel
from typing import Optional


class NotePrivateBase(BaseModel):
    username: str
    note: str


class NotePrivateCreate(NotePrivateBase):
    pass


class NotePrivateRead(NotePrivateBase):
    id: int


class NotePrivateUpdate(BaseModel):
    username: Optional[str] = None
    note: Optional[str] = None
