from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy.dialects.postgresql import JSON
from pydantic import BaseModel

import sys
import os
if os.getenv("GITHUB_ACTIONS"): sys.path.append(os.path.dirname(__file__)) 
from models.progetto_fornitore_link import ProgettoFornitoreLink  
from models.clienti import Cliente
if TYPE_CHECKING:
    from models.fornitori import Fornitore 

class Progetti(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tecnico: str = Field(..., nullable=False)
    progetto_id: Optional[str] = Field(default=None, nullable=True)
    azienda: Optional[str] = Field(default=None, nullable=True)
    centro_di_costo: Optional[str] = Field(default=None, nullable=True)
    commerciale: Optional[str] = Field(default=None, nullable=True)
    stato: str = Field(..., nullable=False)
    cliente_id: int = Field(..., foreign_key="cliente.id", nullable=False)
    data_creazione: datetime = Field(..., nullable=False)
    importo: float = Field(..., nullable=False)
    importo_parz: float = Field(..., nullable=True)
    note: Optional[str] = Field(default=None, nullable=True) 
    data_cambiamento_stato: Optional[datetime] = Field(default=None, nullable=True)    
    taglia_progetto: Optional[str] = Field(default="", nullable=True)
    note_taglia: Optional[str] = Field(default="", nullable=True)
    status_percent: Optional[float] = Field(default=None, nullable=True, index=True)
    fornitori: List["Fornitore"] = Relationship( # Relationship to Fornitore through ProgettoFornitoreLink, not physical column
        back_populates="progetti",
        link_model=ProgettoFornitoreLink
    )
    upload_id: Optional[str] = Field(default=None,nullable=True,index=True)
    upload_id_progetto_files: Optional[str] = Field(default=None,nullable=True,index=True)

    cliente: Optional["Cliente"] = Relationship(back_populates="progetti")    
    fornitori_links: List["ProgettoFornitoreLink"] = Relationship(back_populates="progetto")


class ClienteExport(BaseModel):
    nome_cliente: Optional[str] = None
    tecnico: Optional[str] = None


class ProgettoExport(BaseModel):
    id: Optional[int] = None
    nome_cliente: Optional[str] = None
    cliente: Optional[ClienteExport] = None

    tecnico: Optional[str] = None
    commerciale: Optional[str] = None
    centro_di_costo: Optional[str] = None
    azienda: Optional[str] = None
    stato: Optional[str] = None

    display_date: Optional[str] = None
    data_creazione: Optional[str] = None

    importo: Optional[float] = None
    importo_parz: Optional[float] = None


class ExportExcelRequest(BaseModel):
    projects: List[ProgettoExport]
