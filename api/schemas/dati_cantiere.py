from pydantic import BaseModel
from typing import Optional


class CantiereExtractorBase(BaseModel):
    progetto_id: Optional[int] = None
    campo: Optional[str] = None
    valore: Optional[str] = None


class CantiereExtractorCreate(CantiereExtractorBase):
    pass


class CantiereExtractorUpdate(BaseModel):
    progetto_id: Optional[int] = None
    campo: Optional[str] = None
    valore: Optional[str] = None


class CantiereExtractorRead(CantiereExtractorBase):
    id: int

    class Config:
        from_attributes = True
