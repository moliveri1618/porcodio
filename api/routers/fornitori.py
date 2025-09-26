# Defines API routes and endpoints related to fornitori

from fastapi import APIRouter, Depends, HTTPException
import sys
import os
from typing import List
from sqlmodel import Session, select
import httpx
from datetime import datetime, timezone

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

# Test endpoint to verify external API connectivity
DEFAULTS_FOR_FORNITORE = dict(
    citta="",
    indirizzo="",
    numero_tel="",
    sito="",
    contatti={},
    note="",
    file_info={"file_name": "", "folder_path": "", "full_key": ""},
    upload_id="",
)

@router.post("/import-from-api")
def import_from_gesty(db: Session = Depends(get_db)):
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    r = httpx.get(API_URL, headers=headers, timeout=30.0)
    
    try:
        payload = r.json()
    except ValueError:
        raise HTTPException(status_code=502, detail=f"Upstream returned non-JSON: {r.text[:300]}")

    if r.status_code != 200 or not isinstance(payload, dict) or "data" not in payload:
        raise HTTPException(status_code=502, detail=f"Unexpected upstream response: {payload}")

    items = payload["data"]
    if not isinstance(items, list):
        raise HTTPException(status_code=502, detail="Upstream 'data' is not a list")

    created = 0
    updated = 0
    skipped = 0
    for item in items:
        try:
            fid = int(item["id"])
            nome = (item.get("nome_it") or "").strip()
            if not nome:
                skipped += 1
                continue
        except Exception:
            skipped += 1
            continue

        existing = db.get(Fornitore, fid)
        if existing:
            skipped += 1
        else:
            db.add(
                Fornitore(
                    id=fid,
                    nome_cliente=nome,
                    data_creazione=datetime.now(timezone.utc),
                    **DEFAULTS_FOR_FORNITORE,
                )
            )
            created += 1

    db.commit()
    return {
        "status": "ok",
        "source_count": len(items),
        "created": created,
        "updated": updated,
        "skipped": skipped,
    }

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

