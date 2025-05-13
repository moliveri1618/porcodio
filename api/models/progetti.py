from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from typing import Optional

class Progetti(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tecnico: str = Field(..., nullable=False)
    stato: str = Field(..., nullable=False)
    cliente_id: int = Field(..., foreign_key="cliente.id", nullable=False)
    fornitore_id: int = Field(..., foreign_key="fornitore.id", nullable=False)
    data_creazione: datetime = Field(..., nullable=False)
    importo: float = Field(..., nullable=False)
    file_info: Optional[dict] = Field(
        default=None,
        nullable=True,
        sa_type=JSON,
        description="S3 file metadata: {'file_name': str, 'folder_path': str, 'full_key': str}"
    )