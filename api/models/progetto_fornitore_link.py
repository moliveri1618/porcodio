from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
from typing import Optional, List

class ProdottoFornitore(SQLModel):
    nome: str
    quantita: int

class ProgettoFornitoreLink(SQLModel, table=True):
    progetto_id: int = Field(foreign_key="progetti.id", primary_key=True)
    fornitore_id: int = Field(foreign_key="fornitore.id", primary_key=True)

    contratti: Optional[List[str]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="List of S3 file metadata for contracts"
    )

    rilievi_misure: Optional[List[str]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="List of S3 file metadata for measurement reports"
    )
    
    prodotti_fornitore: Optional[List[ProdottoFornitore]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="List of products provided by the supplier with quantity"
    )