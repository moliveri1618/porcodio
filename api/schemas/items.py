# schemas/items.py
from pydantic import BaseModel

class ItemCreate(BaseModel):
    type: str
    owner: str

class ItemRead(ItemCreate):
    id: int