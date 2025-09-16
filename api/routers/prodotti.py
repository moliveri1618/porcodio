# routers/prodotti.py
# Defines API routes and endpoints related to prodotto

from fastapi import APIRouter, Depends, HTTPException
import sys
import os
from typing import List
from sqlmodel import Session, select

# Allow relative imports when running in GitHub Actions like your example
if os.getenv("GITHUB_ACTIONS"):
    sys.path.append(os.path.dirname(__file__))

from models.prodotti import Prodotto
from schemas.prodotti import ProdottoCreate, ProdottoRead, ProdottoUpdate
from dependecies import get_db 

router = APIRouter()

# Create
@router.post("", response_model=ProdottoRead, status_code=201)
def create_prodotto(prodotto: ProdottoCreate, db: Session = Depends(get_db)):
    db_prodotto = Prodotto(**prodotto.dict())
    db.add(db_prodotto)
    db.commit()
    db.refresh(db_prodotto)
    return db_prodotto

# Get all
@router.get("", response_model=List[ProdottoRead])
def read_prodotti(db: Session = Depends(get_db)):
    prodotti = db.exec(select(Prodotto)).all()
    return prodotti

# Get one
@router.get("/{prodotto_id}", response_model=ProdottoRead)
def read_prodotto(prodotto_id: int, db: Session = Depends(get_db)):
    prodotto = db.get(Prodotto, prodotto_id)
    if not prodotto:
        raise HTTPException(status_code=404, detail="Prodotto not found")
    return prodotto

# Put (full/partial update supported via exclude_unset)
@router.put("/{prodotto_id}", response_model=ProdottoRead)
def update_prodotto(prodotto_id: int, prodotto_update: ProdottoUpdate, db: Session = Depends(get_db)):
    prodotto = db.get(Prodotto, prodotto_id)
    if not prodotto:
        raise HTTPException(status_code=404, detail="Prodotto not found")
    update_data = prodotto_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prodotto, key, value)
    db.add(prodotto)
    db.commit()
    db.refresh(prodotto)
    return prodotto

# Delete
@router.delete("/{prodotto_id}", status_code=204)
def delete_prodotto(prodotto_id: int, db: Session = Depends(get_db)):
    prodotto = db.get(Prodotto, prodotto_id)
    if not prodotto:
        raise HTTPException(status_code=404, detail="Prodotto not found")
    db.delete(prodotto)
    db.commit()
