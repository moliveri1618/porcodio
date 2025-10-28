from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy.dialects.postgresql import JSON

import sys
import os
if os.getenv("GITHUB_ACTIONS"): sys.path.append(os.path.dirname(__file__)) 
from models.progetto_fornitore_link import ProgettoFornitoreLink  # real class import
if TYPE_CHECKING:
    from models.fornitori import Fornitore  # type-only import

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
    fornitori: List["Fornitore"] = Relationship( # Relationship to Fornitore through ProgettoFornitoreLink, not physical column
        back_populates="progetti",
        link_model=ProgettoFornitoreLink
    )
    upload_id: Optional[str] = Field(default=None,nullable=True,index=True)
    upload_id_progetto_files: Optional[str] = Field(default=None,nullable=True,index=True)
    
    cliente: Optional["Cliente"] = Relationship(back_populates="progetti")    
    fornitori_links: List["ProgettoFornitoreLink"] = Relationship(back_populates="progetto")
