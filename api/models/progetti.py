from sqlmodel import SQLModel, Field
from datetime import datetime

class Progetti(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tecnico: str = Field(..., nullable=False)
    stato: str = Field(..., nullable=False)
    cliente_id: int = Field(..., foreign_key="cliente.id", nullable=False)
    fornitore_id: int = Field(..., foreign_key="fornitore.id", nullable=False)
    data_creazione: datetime = Field(..., nullable=False)
    importo: float = Field(..., nullable=False)
