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
    stato: str = Field(..., nullable=False)
    cliente_id: int = Field(..., foreign_key="cliente.id", nullable=False)
    data_creazione: datetime = Field(..., nullable=False)
    importo: float = Field(..., nullable=False)
    fornitori: List["Fornitore"] = Relationship( # Relationship to Fornitore through ProgettoFornitoreLink, not physical column
        back_populates="progetti",
        link_model=ProgettoFornitoreLink
    )
