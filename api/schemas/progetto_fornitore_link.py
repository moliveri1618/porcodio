from pydantic import BaseModel
from typing import Optional, List

class FileInfo(BaseModel):
    file_name: str
    folder_path: str
    full_key: str


class ProgettoFornitoreLinkCreate(BaseModel):
    progetto_id: int
    fornitore_id: int
    contratti: Optional[List[str]] = []
    rilievi_misure: Optional[List[str]] = []

class ProgettoFornitoreLinkRead(ProgettoFornitoreLinkCreate):
    pass 

class ProgettoFornitoreLinkUpdate(BaseModel):
    contratti: Optional[List[str]] = None
    rilievi_misure: Optional[List[str]] = None
