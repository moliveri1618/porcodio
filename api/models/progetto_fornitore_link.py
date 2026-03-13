from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON
from typing import Optional, List, TYPE_CHECKING

import sys
import os
if os.getenv("GITHUB_ACTIONS"):
    sys.path.append(os.path.dirname(__file__))

if TYPE_CHECKING:
    from models.fornitori import Fornitore
    from models.progetti import Progetti


class ProdottoFornitore(SQLModel):
    nome: str
    quantita: int

class ProgettoFornitoreLink(SQLModel, table=True):
    progetto_id: int = Field(foreign_key="progetti.id", primary_key=True)
    fornitore_id: int = Field(foreign_key="fornitore.id", primary_key=True)

    contratti: Optional[List[dict]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="List of S3 file metadata for contracts"
    )

    rilievi_misure: Optional[List[dict]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="List of S3 file metadata for measurement reports"
    )
    
    prodotti_fornitore: Optional[List[ProdottoFornitore]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="List of products provided by the supplier with quantity"
    )
    
    note: Optional[str] = Field(default=None, nullable=True) 
    
    progetto: Optional["Progetti"] = Relationship(back_populates="fornitori_links")
    fornitore: Optional["Fornitore"] = Relationship(back_populates="progetti_links")
