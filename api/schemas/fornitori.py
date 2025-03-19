from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class FornitoriCreate(BaseModel):
    nome_cliente: str
    citta: str  # New field for "citta"
    indirizzo: str
    numero_tel: str  # New field for "numero_tel"
    sito: str  # New field for "sito"
    contatti: Optional[Dict[str, Any]] = None  # New field for contact details (JSON)
    note: Optional[str] = None  # New field for "note"
    data_creazione: datetime

class FornitoriRead(FornitoriCreate):
    id: int  # Read model now includes 'id'

class FornitoriUpdate(BaseModel):
    nome_cliente: Optional[str] = None
    citta: Optional[str] = None
    indirizzo: Optional[str] = None
    numero_tel: Optional[str] = None
    sito: Optional[str] = None  # New field for "sito"
    contatti: Optional[Dict[str, Any]] = None
    note: Optional[str] = None
    data_creazione: Optional[datetime] = None
