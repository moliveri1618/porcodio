# routers/tipo_prodotto.py
# Defines API routes and endpoints related to tipo prodotto

from fastapi import APIRouter, Depends, HTTPException
import sys
import os
from typing import List
from sqlmodel import Session, select

if os.getenv("GITHUB_ACTIONS"):
    sys.path.append(os.path.dirname(__file__))

from models.tipo_prodotto import TipoProdotto
from schemas.tipo_prodotto import (
    TipoProdottoCreate,
    TipoProdottoRead,
    TipoProdottoUpdate,
)
from dependecies import get_db

router = APIRouter()


# Create
@router.post("", response_model=TipoProdottoRead, status_code=201)
def create_tipo_prodotto(
    tipo_prodotto: TipoProdottoCreate,
    db: Session = Depends(get_db),
):
    db_tipo_prodotto = TipoProdotto(**tipo_prodotto.dict())
    db.add(db_tipo_prodotto)
    db.commit()
    db.refresh(db_tipo_prodotto)
    return db_tipo_prodotto


# Get all
@router.get("", response_model=List[TipoProdottoRead])
def read_tipi_prodotto(db: Session = Depends(get_db)):
    tipi_prodotto = db.exec(select(TipoProdotto)).all()
    return tipi_prodotto


# Get one
@router.get("/{tipo_prodotto_id}", response_model=TipoProdottoRead)
def read_tipo_prodotto(
    tipo_prodotto_id: int,
    db: Session = Depends(get_db),
):
    tipo_prodotto = db.get(TipoProdotto, tipo_prodotto_id)

    if not tipo_prodotto:
        raise HTTPException(
            status_code=404,
            detail="Tipo prodotto not found",
        )

    return tipo_prodotto


# Put
@router.put("/{tipo_prodotto_id}", response_model=TipoProdottoRead)
def update_tipo_prodotto(
    tipo_prodotto_id: int,
    tipo_prodotto_update: TipoProdottoUpdate,
    db: Session = Depends(get_db),
):
    tipo_prodotto = db.get(TipoProdotto, tipo_prodotto_id)

    if not tipo_prodotto:
        raise HTTPException(
            status_code=404,
            detail="Tipo prodotto not found",
        )

    update_data = tipo_prodotto_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(tipo_prodotto, key, value)

    db.add(tipo_prodotto)
    db.commit()
    db.refresh(tipo_prodotto)

    return tipo_prodotto


# Delete
@router.delete("/{tipo_prodotto_id}", status_code=204)
def delete_tipo_prodotto(
    tipo_prodotto_id: int,
    db: Session = Depends(get_db),
):
    tipo_prodotto = db.get(TipoProdotto, tipo_prodotto_id)

    if not tipo_prodotto:
        raise HTTPException(
            status_code=404,
            detail="Tipo prodotto not found",
        )

    db.delete(tipo_prodotto)
    db.commit()
