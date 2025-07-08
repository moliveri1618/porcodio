from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
import sys
import os

if os.getenv("GITHUB_ACTIONS"): sys.path.append(os.path.dirname(__file__)) 
from models.progetto_fornitore_link import ProgettoFornitoreLink
from schemas.progetto_fornitore_link import (
    ProgettoFornitoreLinkCreate,
    ProgettoFornitoreLinkRead,
    ProgettoFornitoreLinkUpdate
)
from dependecies import get_db
from typing import List

router = APIRouter()

# Create a link
@router.post("/", response_model=ProgettoFornitoreLinkRead)
def create_link(link: ProgettoFornitoreLinkCreate, db: Session = Depends(get_db)):
    db_link = ProgettoFornitoreLink(**link.model_dump())
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

# Get all links for a specific progetto
@router.get("/progetto/{progetto_id}", response_model=List[ProgettoFornitoreLinkRead])
def get_links_for_progetto(progetto_id: int, db: Session = Depends(get_db)):
    results = db.exec(
        select(ProgettoFornitoreLink).where(ProgettoFornitoreLink.progetto_id == progetto_id)
    ).all()
    return results

# Update files for a specific link
@router.put("/", response_model=ProgettoFornitoreLinkRead)
def update_link(link: ProgettoFornitoreLinkUpdate, progetto_id: int, fornitore_id: int, db: Session = Depends(get_db)):
    db_link = db.get(ProgettoFornitoreLink, (progetto_id, fornitore_id))
    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")
    link_data = link.model_dump(exclude_unset=True)
    for k, v in link_data.items():
        setattr(db_link, k, v)
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link
