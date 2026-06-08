# routers/scheda_tecnica_schema.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlmodel import Session, select

from models.scheda_tecnica_schema import SchedaTecnicaSchema
from schemas.scheda_tecnica_schema import (
    SchedaTecnicaSchemaCreate,
    SchedaTecnicaSchemaRead,
    SchedaTecnicaSchemaUpdate,
)
from dependecies import get_db

router = APIRouter()


@router.post("", response_model=SchedaTecnicaSchemaRead, status_code=201)
def create_scheda_tecnica(
    scheda: SchedaTecnicaSchemaCreate,
    db: Session = Depends(get_db),
):
    db_scheda = SchedaTecnicaSchema(**scheda.model_dump())

    db.add(db_scheda)
    db.commit()
    db.refresh(db_scheda)

    return db_scheda


@router.get("", response_model=List[SchedaTecnicaSchemaRead])
def read_schede_tecniche(db: Session = Depends(get_db)):
    return db.exec(select(SchedaTecnicaSchema)).all()


@router.get("/{scheda_id}", response_model=SchedaTecnicaSchemaRead)
def read_scheda_tecnica(
    scheda_id: int,
    db: Session = Depends(get_db),
):
    scheda = db.get(SchedaTecnicaSchema, scheda_id)

    if not scheda:
        raise HTTPException(status_code=404, detail="Scheda tecnica not found")

    return scheda


@router.put("/{scheda_id}", response_model=SchedaTecnicaSchemaRead)
def update_scheda_tecnica(
    scheda_id: int,
    scheda_update: SchedaTecnicaSchemaUpdate,
    db: Session = Depends(get_db),
):
    scheda = db.get(SchedaTecnicaSchema, scheda_id)

    if not scheda:
        raise HTTPException(status_code=404, detail="Scheda tecnica not found")

    update_data = scheda_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(scheda, key, value)

    db.add(scheda)
    db.commit()
    db.refresh(scheda)

    return scheda


@router.delete("/{scheda_id}", status_code=204)
def delete_scheda_tecnica(
    scheda_id: int,
    db: Session = Depends(get_db),
):
    scheda = db.get(SchedaTecnicaSchema, scheda_id)

    if not scheda:
        raise HTTPException(status_code=404, detail="Scheda tecnica not found")

    db.delete(scheda)
    db.commit()
    return None
