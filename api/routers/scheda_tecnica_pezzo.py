# routers/scheda_tecnica_pezzo.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlmodel import Session, select

from models.scheda_tecnica_pezzo import SchedaTecnicaPezzo
from schemas.scheda_tecnica_pezzo import (
    SchedaTecnicaPezzoCreate,
    SchedaTecnicaPezzoRead,
    SchedaTecnicaPezzoUpdate,
)
from dependecies import get_db

router = APIRouter()


# Create
@router.post("", response_model=SchedaTecnicaPezzoRead, status_code=201)
def create_scheda_tecnica_pezzo(
    scheda: SchedaTecnicaPezzoCreate,
    db: Session = Depends(get_db),
):
    db_scheda = SchedaTecnicaPezzo(**scheda.dict())
    db.add(db_scheda)
    db.commit()
    db.refresh(db_scheda)
    return db_scheda


# Get all
@router.get("", response_model=List[SchedaTecnicaPezzoRead])
def read_schede_tecniche_pezzi(db: Session = Depends(get_db)):
    schede = db.exec(select(SchedaTecnicaPezzo)).all()
    return schede


# Get one
@router.get("/{scheda_id}", response_model=SchedaTecnicaPezzoRead)
def read_scheda_tecnica_pezzo(
    scheda_id: int,
    db: Session = Depends(get_db),
):
    scheda = db.get(SchedaTecnicaPezzo, scheda_id)

    if not scheda:
        raise HTTPException(status_code=404, detail="Scheda tecnica pezzo not found")

    return scheda


# Put
@router.put("/{scheda_id}", response_model=SchedaTecnicaPezzoRead)
def update_scheda_tecnica_pezzo(
    scheda_id: int,
    scheda_update: SchedaTecnicaPezzoUpdate,
    db: Session = Depends(get_db),
):
    scheda = db.get(SchedaTecnicaPezzo, scheda_id)

    if not scheda:
        raise HTTPException(status_code=404, detail="Scheda tecnica pezzo not found")

    update_data = scheda_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(scheda, key, value)

    db.add(scheda)
    db.commit()
    db.refresh(scheda)

    return scheda


# Delete
@router.delete("/{scheda_id}", status_code=204)
def delete_scheda_tecnica_pezzo(
    scheda_id: int,
    db: Session = Depends(get_db),
):
    scheda = db.get(SchedaTecnicaPezzo, scheda_id)

    if not scheda:
        raise HTTPException(status_code=404, detail="Scheda tecnica pezzo not found")

    db.delete(scheda)
    db.commit()
