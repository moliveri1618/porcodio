from typing import Optional, Dict, Any, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from sqlalchemy import JSON, Column
from sqlalchemy import Integer

class Cliente(SQLModel, table=True):
    id: int = Field(sa_column=Column(Integer, primary_key=True, autoincrement=False))
    nome_cliente: str = Field(..., nullable=False)  # "nome_cliente" remains the same
    citta: str = Field(..., nullable=False)  # New field for "citta"
    indirizzo: str = Field(..., nullable=False)  # "indirizzo" remains the same
    numero_tel: str = Field(..., nullable=False)  # New field for "numero_tel"
    centro_di_costo: str = Field(..., nullable=False)  # "centro_di_costo" remains the same
    contatti: Optional[Dict[str, Any]] = Field(
        default=None, 
        sa_column=Column(JSON, nullable=True)
    )
    note: Optional[str] = Field(default=None, nullable=True)  # New field for "note"
    data_creazione: datetime = Field(..., nullable=False)  # "data_creazione" remains the same

    progetti: List["Progetti"] = Relationship(back_populates="cliente")