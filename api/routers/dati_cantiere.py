from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from dependecies import get_db
from models.dati_cantiere import CantiereExtractor
from schemas.dati_cantiere import (
    CantiereExtractorCreate,
    CantiereExtractorRead,
)

router = APIRouter()


@router.get("/by-progetto/{progetto_id}", response_model=list[CantiereExtractorRead])
def get_all_by_progetto_id(
    progetto_id: int,
    db: Session = Depends(get_db),
):
    rows = db.exec(
        select(CantiereExtractor)
        .where(CantiereExtractor.progetto_id == progetto_id)
        .order_by(CantiereExtractor.id.asc())
    ).all()

    return rows


@router.post("/bulk-upsert/{progetto_id}", response_model=list[CantiereExtractorRead])
def bulk_upsert_by_progetto_id(
    progetto_id: int,
    items: List[CantiereExtractorCreate],
    db: Session = Depends(get_db),
):
    saved_rows = []

    for item in items:
        campo = item.campo

        existing = db.exec(
            select(CantiereExtractor).where(
                CantiereExtractor.progetto_id == progetto_id,
                CantiereExtractor.campo == campo,
            )
        ).first()

        if existing:
            existing.valore = item.valore
            row = existing
        else:
            row = CantiereExtractor(
                progetto_id=progetto_id,
                campo=campo,
                valore=item.valore,
            )
            db.add(row)

        saved_rows.append(row)

    db.commit()

    for row in saved_rows:
        db.refresh(row)

    return saved_rows
