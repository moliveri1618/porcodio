from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy import JSON, Column

class Fornitore(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nome_cliente: str = Field(..., nullable=False)  # "nome_cliente" remains the same
    citta: str = Field(..., nullable=False)  # New field for "citta"
    indirizzo: str = Field(..., nullable=False)  # "indirizzo" remains the same
    numero_tel: str = Field(..., nullable=False)  # New field for "numero_tel"
    sito: str = Field(..., nullable=False)  # New field for "sito"
    contatti: Optional[Dict[str, Any]] = Field(
        default=None, 
        sa_column=Column(JSON, nullable=True)  # Storing as JSON
    )
    note: Optional[str] = Field(default=None, nullable=True)  # New field for "note"
    data_creazione: datetime = Field(..., nullable=False)  # "data_creazione" remains the same
