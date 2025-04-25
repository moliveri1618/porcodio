# schemas/progetti.py
from pydantic import BaseModel
from datetime import datetime

class ProgettiCreate(BaseModel):
    tecnico: str  
    stato: str
    data_creazione: datetime
    importo: float
    cliente_id: int

class ProgettiRead(ProgettiCreate):
    id: int

class ProgettiUpdate(BaseModel):
    tecnico: str | None = None
    stato: str | None = None
    data_creazione: datetime | None = None
    importo: float | None = None
    cliente_id: int
