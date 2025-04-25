# Defines API routes and endpoints related to progetti

from fastapi import APIRouter, Depends, HTTPException
import sys
import os
from typing import List
from sqlmodel import Session, select

if os.getenv("GITHUB_ACTIONS"): sys.path.append(os.path.dirname(__file__)) 
from models.progetti import Progetti
from models.clienti import Cliente
from models.fornitori import Fornitore
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
@router.get("")
def read_progetti(db: Session = Depends(get_db)):
    stmt = (
            select(Progetti, Cliente, Fornitore)
            .join(Cliente, Progetti.cliente_id == Cliente.id, isouter=True)
            .join(Fornitore, Progetti.fornitore_id == Fornitore.id, isouter=True)

        )
    results = db.exec(stmt).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="Progetto not found")

    progetti_client_fornitori_dict = []
    for progetto, cliente, fornitore  in results:
        cliente_dict = {
            "id": cliente.id,
            "nome_cliente": cliente.nome_cliente,
            "citta": cliente.citta,
            "indirizzo": cliente.indirizzo,
            "numero_tel": cliente.numero_tel,
            "centro_di_costo": cliente.centro_di_costo,
            "contatti": cliente.contatti,
            "note": cliente.note,
            "data_creazione_cliente": cliente.data_creazione,
        } if cliente else {}
        
        fornitore_dict = {
            "id": fornitore.id,
            "nome_fornitore": fornitore.nome_cliente,
            "indirizzo": fornitore.indirizzo,
            "citta": fornitore.citta,
            "numero_tel": fornitore.numero_tel,
            "sito": fornitore.sito,
            "contatti": fornitore.contatti,
            "data_creazione_fornitore": fornitore.data_creazione,
        } if fornitore else {}

        progetti_client_fornitori_dict.append({
            "id": progetto.id,
            "tecnico": progetto.tecnico,
            "stato": progetto.stato,
            "cliente_id": progetto.cliente_id,
            "data_creazione": progetto.data_creazione,
            "importo": progetto.importo,
            "cliente": cliente_dict,
            "fornitore": fornitore_dict
        })

    return progetti_client_fornitori_dict

# Get one
@router.get("/{progetto_id}")
def read_progetto(progetto_id: int, db: Session = Depends(get_db)):
    stmt = (
        select(Progetti, Cliente, Fornitore)
        .join(Cliente, Progetti.cliente_id == Cliente.id, isouter=True)
        .join(Fornitore, Progetti.fornitore_id == Fornitore.id, isouter=True)
        .where(Progetti.id == progetto_id)
    )
    result = db.exec(stmt).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Progetto not found")
    
    progetto, cliente, fornitore = result
    
    cliente_dict = {
        "cliente_id": progetto.cliente_id,
        "nome_cliente": cliente.nome_cliente if cliente else None,
        "citta": cliente.citta if cliente else None,
        "indirizzo": cliente.indirizzo if cliente else None,
        "numero_tel": cliente.numero_tel if cliente else None,
        "centro_di_costo": cliente.centro_di_costo if cliente else None,
        "contatti": cliente.contatti if cliente else None,
        "note": cliente.note if cliente else None,
        "data_creazione_cliente": cliente.data_creazione if cliente else None,
    }
    
    fornitore_dict = {
        "fornitore_id": progetto.fornitore_id,
        "nome_fornitore": fornitore.nome_cliente if fornitore else None,
        "indirizzo": fornitore.indirizzo if fornitore else None,
        "citta": fornitore.citta if fornitore else None,
        "numero_tel": fornitore.numero_tel if fornitore else None,
        "sito": fornitore.sito if fornitore else None,
        "contatti": fornitore.contatti if fornitore else None,
        "data_creazione_fornitore": fornitore.data_creazione if fornitore else None,
    }

    return {
        "progetto_id": progetto.id,
        "tecnico": progetto.tecnico,
        "stato": progetto.stato,
        "data_creazione": progetto.data_creazione,
        "importo": progetto.importo,
        "cliente": cliente_dict,
        "fornitore": fornitore_dict 
    }

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
