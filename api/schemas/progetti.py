# schemas/progetti.py
from pydantic import BaseModel
from datetime import datetime

class ProgettiCreate(BaseModel):
    nome_cliente: str
    status: str
    tecnico: str  # This field must be included
    stato: str
    fornitori: str
    centro_di_costo: str
    indirizzo: str
    data_creazione: datetime
    importo: float

class ProgettiRead(ProgettiCreate):
    id: int

class ProgettiUpdate(BaseModel):
    nome_cliente: str | None = None
    status: str | None = None
    tecnico: str | None = None
    stato: str | None = None
    fornitori: str | None = None
    centro_di_costo: str | None = None
    indirizzo: str | None = None
    data_creazione: datetime | None = None
    importo: float | None = None
