from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from sqlalchemy import JSON, Column
from typing import List, TYPE_CHECKING
import sys
import os

if os.getenv("GITHUB_ACTIONS"): sys.path.append(os.path.dirname(__file__)) 
from models.progetto_fornitore_link import ProgettoFornitoreLink  # real class import
if TYPE_CHECKING:
    from models.progetti import Progetti
    
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
    file_info: Optional[dict] = Field(
        default=None,
        nullable=True,
        sa_type=JSON,
        description="S3 file metadata: {'file_name': str, 'folder_path': str, 'full_key': str}"
    )
    progetti: List["Progetti"] = Relationship(
        back_populates="fornitori",
        link_model=ProgettoFornitoreLink
    )
    upload_id: Optional[str] = Field(default=None,nullable=True,index=True)

    progetti_links: List["ProgettoFornitoreLink"] = Relationship(back_populates="fornitore")
