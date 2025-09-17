# schemas/progetti.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ProdottoFornitore(BaseModel):
    nome: str
    quantita: int

class FileInfo(BaseModel):
    file_name: str
    folder_path: str
    full_key: str
    
class FornitoreLinkData(BaseModel):
    fornitore_id: int
    contratti: Optional[List[FileInfo]] = []
    rilievi_misure: Optional[List[FileInfo]] = []
    prodotti_fornitore: Optional[List[ProdottoFornitore]] = []  


class ProgettiCreate(BaseModel):
    tecnico: str  
    azienda: Optional[str] = None 
    centro_di_costo: Optional[str] = None
    stato: str
    data_creazione: datetime
    importo: float
    cliente_id: int
    fornitori: List[FornitoreLinkData]  
    upload_id: Optional[str] = None
    upload_id_progetto_files: Optional[str] = None


class FornitoreInProgetto(BaseModel):
    id: int
    nome_cliente: str
    citta: str
    indirizzo: str
    numero_tel: str
    sito: str

class ProgettiRead(ProgettiCreate):
    id: int
    fornitori: Optional[List[FornitoreInProgetto]] = None  # ✅ optional for expanded read

class ProgettiUpdate(BaseModel):
    tecnico: Optional[str] = None
    azienda: Optional[str] = None 
    centro_di_costo: Optional[str] = None
    stato: Optional[str] = None
    data_creazione: Optional[datetime] = None
    importo: Optional[float] = None
    cliente_id: Optional[int] = None
    fornitori: Optional[List[FornitoreLinkData]] = None
    upload_id: Optional[str] = None
    upload_id_progetto_files: Optional[str] = None
