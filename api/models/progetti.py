from sqlmodel import SQLModel, Field
from datetime import datetime

class Progetti(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tecnico: str = Field(..., nullable=False)
    stato: str = Field(..., nullable=False)
    data_creazione: datetime = Field(..., nullable=False)
    importo: float = Field(..., nullable=False)
