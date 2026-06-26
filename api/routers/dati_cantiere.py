from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from dependecies import get_db
from models.dati_cantiere import DatiCantiere
from schemas.dati_cantiere import (
    DatiCantiereCreate,
    DatiCantiereRead,
)

router = APIRouter()


@router.get("/by-progetto/{progetto_id}", response_model=DatiCantiereRead | None)
def get_by_progetto_id(
    progetto_id: int,
    db: Session = Depends(get_db),
):
    row = db.exec(
        select(DatiCantiere).where(DatiCantiere.progetto_id == progetto_id)
    ).first()

    return row



@router.post("/upsert/{progetto_id}", response_model=DatiCantiereRead)
def upsert_by_progetto_id(
    progetto_id: int,
    item: DatiCantiereCreate,
    db: Session = Depends(get_db),
):
    existing = db.exec(
        select(DatiCantiere).where(DatiCantiere.progetto_id == progetto_id)
    ).first()

    data = item.model_dump(exclude_unset=True)
    data["progetto_id"] = progetto_id

    if existing:
        for key, value in data.items():
            setattr(existing, key, value)

        row = existing
    else:
        row = DatiCantiere(**data)
        db.add(row)

    db.commit()
    db.refresh(row)

    return row
