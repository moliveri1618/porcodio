# routers/tipo_prodotto_valori.py
# Defines API routes and endpoints related to tipo prodotto valori

from fastapi import APIRouter, Depends, HTTPException
import sys
import os
from typing import List
from sqlmodel import Session, select

if os.getenv("GITHUB_ACTIONS"):
    sys.path.append(os.path.dirname(__file__))

from models.tipo_prodotto_valori import TipoProdottoValori
from schemas.tipo_prodotto_valori import (
    TipoProdottoValoriCreate,
    TipoProdottoValoriRead,
    TipoProdottoValoriUpdate,
)
from dependecies import get_db

router = APIRouter()


# Create
@router.post("", response_model=TipoProdottoValoriRead, status_code=201)
def create_tipo_prodotto(
    tipo_prodotto: TipoProdottoValoriCreate,
    db: Session = Depends(get_db),
):
    db_tipo_prodotto = TipoProdottoValori(**tipo_prodotto.dict())
    db.add(db_tipo_prodotto)
    db.commit()
    db.refresh(db_tipo_prodotto)
    return db_tipo_prodotto


@router.post(
    "/bulk",
    response_model=list[TipoProdottoValoriRead],
    status_code=201,
)
def create_tipo_prodotto_valori_bulk(
    valori: list[TipoProdottoValoriCreate],
    db: Session = Depends(get_db),
):
    db_valori = [TipoProdottoValori(**valore.dict()) for valore in valori]

    db.add_all(db_valori)
    db.commit()

    for valore in db_valori:
        db.refresh(valore)

    return db_valori


# Get all
@router.get("", response_model=List[TipoProdottoValoriRead])
def read_tipi_prodotto(db: Session = Depends(get_db)):
    tipi_prodotto = db.exec(select(TipoProdottoValori)).all()
    return tipi_prodotto


# Get one
@router.get("/{tipo_prodotto_id}", response_model=TipoProdottoValoriRead)
def read_tipo_prodotto(
    tipo_prodotto_id: int,
    db: Session = Depends(get_db),
):
    tipo_prodotto = db.get(TipoProdottoValori, tipo_prodotto_id)

    if not tipo_prodotto:
        raise HTTPException(
            status_code=404,
            detail="Tipo prodotto not found",
        )

    return tipo_prodotto


# Put
@router.put("/{tipo_prodotto_id}", response_model=TipoProdottoValoriRead)
def update_tipo_prodotto(
    tipo_prodotto_id: int,
    tipo_prodotto_update: TipoProdottoValoriUpdate,
    db: Session = Depends(get_db),
):
    tipo_prodotto = db.get(TipoProdottoValori, tipo_prodotto_id)

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
    tipo_prodotto = db.get(TipoProdottoValori, tipo_prodotto_id)

    if not tipo_prodotto:
        raise HTTPException(
            status_code=404,
            detail="Tipo prodotto not found",
        )

    db.delete(tipo_prodotto)
    db.commit()
