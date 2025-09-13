# Defines API routes and endpoints related to fornitori

from fastapi import APIRouter, Depends, HTTPException
import sys
import os
from typing import List
from sqlmodel import Session, select
import httpx

if os.getenv("GITHUB_ACTIONS"): sys.path.append(os.path.dirname(__file__)) 
from models.fornitori import Fornitore  # Changed model name from Cliente to Fornitori
from schemas.fornitori import FornitoriCreate, FornitoriRead, FornitoriUpdate  # Updated schemas
from dependecies import get_db

router = APIRouter()

API_BASE = "https://www.tigulliocrm.it/api"
API_URL = "https://www.tigulliocrm.it/api/fornitori/"
API_KEY = "xAe5xrokrKL4g7sbyGHQ3mZ9wyqUVks7"

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
    
    
@router.get("/import-fornitori-from-api")
def import_fornitori_from_gesty():
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    try:
        response = httpx.get(API_URL, headers=headers, timeout=30.0)
        return {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text
        }
    except Exception as e:
        return {"error": str(e)}
