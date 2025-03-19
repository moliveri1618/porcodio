from sqlmodel import SQLModel, Field
from datetime import datetime

class Progetti(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nome_cliente: str = Field(..., nullable=False)
    status: str = Field(..., nullable=False)
    tecnico: str = Field(..., nullable=False)
    stato: str = Field(..., nullable=False)
    fornitori: str = Field(..., nullable=False)
    centro_di_costo: str = Field(..., nullable=False)
    indirizzo: str = Field(..., nullable=False)
    data_creazione: datetime = Field(..., nullable=False)
    importo: float = Field(..., nullable=False)
