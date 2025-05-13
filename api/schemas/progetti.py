# schemas/progetti.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FileInfo(BaseModel):
    file_name: str
    folder_path: str
    full_key: str

class ProgettiCreate(BaseModel):
    tecnico: str  
    stato: str
    data_creazione: datetime
    importo: float
    cliente_id: int
    fornitore_id: int
    file_info: Optional[FileInfo] = None


class ProgettiRead(ProgettiCreate):
    id: int

class ProgettiUpdate(BaseModel):
    tecnico: str | None = None
    stato: str | None = None
    data_creazione: datetime | None = None
    importo: float | None = None
    cliente_id: int
    fornitore_id: int 
    file_info: Optional[FileInfo] = None
