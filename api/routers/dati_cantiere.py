from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlmodel import Session, select
from dependecies import get_db

from models.dati_cantiere import CantiereExtractor
from schemas.dati_cantiere import (
    CantiereExtractorCreate,
    CantiereExtractorRead,
    CantiereExtractorUpdate,
)

router = APIRouter()


# CREATE
@router.post("", response_model=CantiereExtractorRead)
def create_cantiere_extractor(
    data: CantiereExtractorCreate,
    db: Session = Depends(get_db),
):
    db_row = CantiereExtractor(**data.model_dump())

    db.add(db_row)
    db.commit()
    db.refresh(db_row)

    return db_row


# GET ALL
@router.get("", response_model=list[CantiereExtractorRead])
def read_cantiere_extractors(db: Session = Depends(get_db)):
    rows = db.exec(
        select(CantiereExtractor).order_by(CantiereExtractor.id.desc())
    ).all()

    return rows


# GET ONE BY ID
@router.get("/{id}", response_model=CantiereExtractorRead)
def read_cantiere_extractor(
    id: int,
    db: Session = Depends(get_db),
):
    row = db.get(CantiereExtractor, id)

    if not row:
        raise HTTPException(status_code=404, detail="Cantiere extractor not found")

    return row


# GET BY PROGETTO ID
@router.get("/by-progetto/{progetto_id}", response_model=CantiereExtractorRead | None)
def read_cantiere_extractor_by_progetto(
    progetto_id: int,
    db: Session = Depends(get_db),
):
    row = db.exec(
        select(CantiereExtractor).where(CantiereExtractor.progetto_id == progetto_id)
    ).first()

    return row


# UPDATE ONE
@router.put("/{id}", response_model=CantiereExtractorRead)
def update_cantiere_extractor(
    id: int,
    data: CantiereExtractorUpdate,
    db: Session = Depends(get_db),
):
    row = db.get(CantiereExtractor, id)

    if not row:
        raise HTTPException(status_code=404, detail="Cantiere extractor not found")

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(row, key, value)

    db.add(row)
    db.commit()
    db.refresh(row)

    return row


# UPSERT BY PROGETTO ID
@router.post("/by-progetto/{progetto_id}", response_model=CantiereExtractorRead)
def create_or_update_cantiere_extractor_by_progetto(
    progetto_id: int,
    data: CantiereExtractorUpdate,
    db: Session = Depends(get_db),
):
    row = db.exec(
        select(CantiereExtractor).where(CantiereExtractor.progetto_id == progetto_id)
    ).first()

    payload = data.model_dump(exclude_unset=True)
    payload["progetto_id"] = progetto_id

    if row:
        for key, value in payload.items():
            setattr(row, key, value)
    else:
        row = CantiereExtractor(**payload)

    db.add(row)
    db.commit()
    db.refresh(row)

    return row


# DELETE ONE
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cantiere_extractor(
    id: int,
    db: Session = Depends(get_db),
):
    row = db.get(CantiereExtractor, id)

    if not row:
        raise HTTPException(status_code=404, detail="Cantiere extractor not found")

    db.delete(row)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
