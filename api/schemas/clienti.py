from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ClienteCreate(BaseModel):
    nome_cliente: str
    citta: str  # Updated field
    indirizzo: str
    numero_tel: str  # Updated field
    centro_di_costo: str
    contatti: Optional[dict] = None  # New field for contact details (JSON)
    note: Optional[str] = None  # New field for notes
    data_creazione: datetime

class ClienteRead(ClienteCreate):
    id: int  # Read model now includes 'id'

class ClienteUpdate(BaseModel):
    nome_cliente: Optional[str] = None
    citta: Optional[str] = None
    indirizzo: Optional[str] = None
    numero_tel: Optional[str] = None
    centro_di_costo: Optional[str] = None
    contatti: Optional[dict] = None
    note: Optional[str] = None
    data_creazione: Optional[datetime] = None
