# Defines API routes and endpoints related to fornitori

from fastapi import APIRouter, Depends, HTTPException
import sys
import os
from typing import List
from sqlmodel import Session, select

if os.getenv("GITHUB_ACTIONS"): sys.path.append(os.path.dirname(__file__)) 
from models.fornitori import Fornitore  # Changed model name from Cliente to Fornitori
from schemas.fornitori import FornitoriCreate, FornitoriRead, FornitoriUpdate  # Updated schemas
from dependecies import get_db

router = APIRouter()

# Create
@router.post("", response_model=FornitoriRead)
def create_fornitore(fornitore: FornitoriCreate, db: Session = Depends(get_db)):
    db_fornitore = Fornitore(**fornitore.dict())  # Changed to Fornitori model and dict() method
    db.add(db_fornitore)
    db.commit()
    db.refresh(db_fornitore)
    return db_fornitore

# Get all
@router.get("", response_model=List[FornitoriRead])
def read_fornitori(db: Session = Depends(get_db)):
    fornitori = db.exec(select(Fornitore)).all()  # Using Fornitori model to fetch all records
    return fornitori

# Get one
@router.get("/{fornitore_id}", response_model=FornitoriRead)
def read_fornitore(fornitore_id: int, db: Session = Depends(get_db)):
    fornitore = db.get(Fornitore, fornitore_id)  # Fetching a specific Fornitori record by ID
    if not fornitore:
        raise HTTPException(status_code=404, detail="Fornitore not found")
    return fornitore

# Put
@router.put("/{fornitore_id}", response_model=FornitoriRead)
def update_fornitore(fornitore_id: int, fornitore_update: FornitoriUpdate, db: Session = Depends(get_db)):
    fornitore = db.get(Fornitore, fornitore_id)  # Fetch the fornitore to update
    if not fornitore:
        raise HTTPException(status_code=404, detail="Fornitore not found")
    fornitore_data = fornitore_update.dict(exclude_unset=True)  # Changed to dict() method
    for key, value in fornitore_data.items():
        setattr(fornitore, key, value)  # Update the fornitore with new values
    db.add(fornitore)
    db.commit()
    db.refresh(fornitore)
    return fornitore

# Delete
@router.delete("/{fornitore_id}", status_code=204)
def delete_fornitore(fornitore_id: int, db: Session = Depends(get_db)):
    fornitore = db.get(Fornitore, fornitore_id)  # Fetch fornitore to delete
    if not fornitore:
        raise HTTPException(status_code=404, detail="Fornitore not found")
    db.delete(fornitore)
    db.commit()
