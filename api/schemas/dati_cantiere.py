from pydantic import BaseModel
from typing import Optional


class CantiereExtractorBase(BaseModel):
    progetto_id: Optional[int] = None

    # dati_anagrafici
    rag_sociale: Optional[str] = None
    luogo_zona: Optional[str] = None
    consegna: Optional[str] = None
    email: Optional[str] = None
    architetto: Optional[str] = None
    contatto_impresa_edile: Optional[str] = None
    altri_contatti: Optional[str] = None

    # cantiere
    cantiere_tecnico_rilevatore: Optional[str] = None
    cantiere_tempo_installazione: Optional[str] = None
    cantiere_piano_edificio: Optional[str] = None
    casa_abitata: Optional[str] = None
    cantiere_accesso: Optional[str] = None
    cantiere_trasporto: Optional[str] = None
    cantiere_mezzi: Optional[str] = None
    cantiere_tipologia_posa: Optional[str] = None
    cantiere_attrezzatura_particolare: Optional[str] = None
    cantiere_persone_necessarie: Optional[str] = None
    cantiere_note_accesso: Optional[str] = None
    cantiere_materiale_consumo_tagli: Optional[str] = None


class CantiereExtractorCreate(CantiereExtractorBase):
    pass


class CantiereExtractorUpdate(BaseModel):
    progetto_id: Optional[int] = None

    # dati_anagrafici
    rag_sociale: Optional[str] = None
    luogo_zona: Optional[str] = None
    consegna: Optional[str] = None
    email: Optional[str] = None
    architetto: Optional[str] = None
    contatto_impresa_edile: Optional[str] = None
    altri_contatti: Optional[str] = None

    # cantiere
    cantiere_tecnico_rilevatore: Optional[str] = None
    cantiere_tempo_installazione: Optional[str] = None
    cantiere_piano_edificio: Optional[str] = None
    casa_abitata: Optional[str] = None
    cantiere_accesso: Optional[str] = None
    cantiere_trasporto: Optional[str] = None
    cantiere_mezzi: Optional[str] = None
    cantiere_tipologia_posa: Optional[str] = None
    cantiere_attrezzatura_particolare: Optional[str] = None
    cantiere_persone_necessarie: Optional[str] = None
    cantiere_note_accesso: Optional[str] = None
    cantiere_materiale_consumo_tagli: Optional[str] = None


class CantiereExtractorRead(CantiereExtractorBase):
    id: int

    class Config:
        from_attributes = True
