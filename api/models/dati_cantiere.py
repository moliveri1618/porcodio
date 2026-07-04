from typing import Optional
from sqlmodel import SQLModel, Field


class DatiCantiere(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    progetto_id: Optional[int] = Field(
        default=None,
        foreign_key="progetti.id",
        index=True,
    )

    # DATI ANAGRAFICI
    numero: Optional[str] = Field(default=None)
    data: Optional[str] = Field(default=None)
    piva: Optional[str] = Field(default=None)
    pec: Optional[str] = Field(default=None)
    cap: Optional[str] = Field(default=None)
    rag_sociale: Optional[str] = Field(default=None)
    luogo_zona: Optional[str] = Field(default=None)
    consegna: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    architetto: Optional[str] = Field(default=None)
    contatto_impresa_edile: Optional[str] = Field(default=None)
    altri_contatti: Optional[str] = Field(default=None)

    # DATI TECNICI CANTIERE
    cantiere_tecnico_rilevatore: Optional[str] = Field(default=None)
    cantiere_tempo_installazione: Optional[str] = Field(default=None)
    cantiere_piano_edificio: Optional[str] = Field(default=None)
    casa_abitata: Optional[str] = Field(default=None)
    cantiere_accesso: Optional[str] = Field(default=None)
    cantiere_trasporto: Optional[str] = Field(default=None)
    cantiere_mezzi: Optional[str] = Field(default=None)
    cantiere_tipologia_posa: Optional[str] = Field(default=None)
    cantiere_attrezzatura_particolare: Optional[str] = Field(default=None)
    cantiere_persone_necessarie: Optional[str] = Field(default=None)
    cantiere_note_accesso: Optional[str] = Field(default=None)
    cantiere_materiale_consumo_tagli: Optional[str] = Field(default=None)
