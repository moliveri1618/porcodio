# Defines API routes and endpoints related to progetti

from fastapi import APIRouter, Depends, HTTPException
import sys
import os
from typing import List
from sqlmodel import Session, select

if os.getenv("GITHUB_ACTIONS"): sys.path.append(os.path.dirname(__file__)) 
from models.progetti import Progetti
from schemas.progetti import ProgettiCreate, ProgettiRead, ProgettiUpdate
from dependecies import get_db

router = APIRouter()

# Create
@router.post("", response_model=ProgettiRead)
def create_progetto(progetto: ProgettiCreate, db: Session = Depends(get_db)):
    db_progetto = Progetti(**progetto.model_dump())
    db.add(db_progetto)
    db.commit()
    db.refresh(db_progetto)
    return db_progetto

# Get all
@router.get("", response_model=List[ProgettiRead])
def read_progetti(db: Session = Depends(get_db)):
    progetti = db.exec(select(Progetti)).all()
    return progetti

# Get one
@router.get("/{progetto_id}", response_model=ProgettiRead)
def read_progetto(progetto_id: int, db: Session = Depends(get_db)):
    progetto = db.get(Progetti, progetto_id)
    if not progetto:
        raise HTTPException(status_code=404, detail="Progetto not found")
    return progetto

# Put
@router.put("/{progetto_id}", response_model=ProgettiRead)
def update_progetto(progetto_id: int, progetto_update: ProgettiUpdate, db: Session = Depends(get_db)):
    progetto = db.get(Progetti, progetto_id)
    if not progetto:
        raise HTTPException(status_code=404, detail="Progetto not found")
    progetto_data = progetto_update.model_dump(exclude_unset=True)
    for key, value in progetto_data.items():
        setattr(progetto, key, value)
    db.add(progetto)
    db.commit()
    db.refresh(progetto)
    return progetto

# Delete
@router.delete("/{progetto_id}", status_code=204)
def delete_progetto(progetto_id: int, db: Session = Depends(get_db)):
    progetto = db.get(Progetti, progetto_id)
    if not progetto:
        raise HTTPException(status_code=404, detail="Progetto not found")
    db.delete(progetto)
    db.commit()
