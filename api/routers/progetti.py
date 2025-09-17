# Defines API routes and endpoints related to progetti

from fastapi import APIRouter, Depends, HTTPException
import sys
import os
from typing import List
from sqlmodel import Session, select
import httpx

if os.getenv("GITHUB_ACTIONS"): sys.path.append(os.path.dirname(__file__)) 
from models.progetti import Progetti
from models.clienti import Cliente
from models.fornitori import Fornitore
from models.prodotti import Prodotto
from models.progetto_fornitore_link import ProgettoFornitoreLink
from schemas.progetti import ProgettiCreate, ProgettiRead, ProgettiUpdate
from routers.utils import *
from dependecies import get_db

router = APIRouter()

# Create
@router.post("", response_model=ProgettiRead)
def create_progetto(progetto: ProgettiCreate, db: Session = Depends(get_db)):
    
    # 1. Create the Progetto record
    db_progetto = Progetti(
        tecnico=progetto.tecnico,
        stato=progetto.stato,
        cliente_id=progetto.cliente_id,
        data_creazione=progetto.data_creazione,
        importo=progetto.importo,
        upload_id=progetto.upload_id,
        upload_id_progetto_files=progetto.upload_id_progetto_files
    )
    db.add(db_progetto)
    db.commit()
    db.refresh(db_progetto)

    # 2. Create associated ProgettoFornitoreLink entries
    for f in progetto.fornitori:
        link = ProgettoFornitoreLink(
            progetto_id=db_progetto.id,
            fornitore_id=f.fornitore_id,
            contratti=[c.model_dump() for c in f.contratti] if f.contratti else [],
            rilievi_misure=[r.model_dump() for r in f.rilievi_misure] if f.rilievi_misure else [],
            prodotti_fornitore=[p.model_dump() for p in f.prodotti_fornitore] if f.prodotti_fornitore else []  
        )
        db.add(link)

    db.commit()
    db.refresh(db_progetto)
    return db_progetto

# Get from gesty
@router.get("/get_progetti_gesty")
def progetti_from_gesty(db: Session = Depends(get_db)):
    """
    Calls the dip-tecnico API with Bearer token in header
    """
    
    # Get progetti
    payload = fetch_from_gesty("dip-tecnico")
    payload = payload[:5]

    # Extract & Insert Prodotti from Progetti
    #prodotti_inserted_info = extract_prodotti_names(db, payload)
    
    # transform contratto_code & rm code into full proxy URL
    payload = attach_file_links(payload)
    
    # Add new cliente 
    clienti_inserted_info = create_clienti_from_payload(db, payload)
    
    # Build Progetto & Fornitori payload 
    progetti_payload = build_progetti_payloads(payload)
    
    # Insert them into DB using your existing logic
    created_progetti = []
    for body in progetti_payload:
        progetto_in = ProgettiCreate(**body)  
        created = create_progetto(progetto=progetto_in, db=db)
        created_progetti.append(created)
    
    return progetti_payload
    
# Get all
@router.get("")
def read_progetti(db: Session = Depends(get_db)):
    progetti = db.exec(select(Progetti)).all()
    
    if not progetti:
        raise HTTPException(status_code=404, detail="No progetti found")

    result = []
    for progetto in progetti:
        # Get cliente info
        cliente = db.get(Cliente, progetto.cliente_id)
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

        # Get linked fornitori via join table
        links = db.exec(
            select(ProgettoFornitoreLink).where(ProgettoFornitoreLink.progetto_id == progetto.id)
        ).all()

        fornitori_list = []
        for link in links:
            fornitore = db.get(Fornitore, link.fornitore_id)
            if fornitore:
                fornitori_list.append({
                    "id": fornitore.id,
                    "nome_fornitore": fornitore.nome_cliente,
                    "indirizzo": fornitore.indirizzo,
                    "citta": fornitore.citta,
                    "numero_tel": fornitore.numero_tel,
                    "sito": fornitore.sito,
                    "contatti": fornitore.contatti,
                    "data_creazione_fornitore": fornitore.data_creazione,
                    "contratti": link.contratti,
                    "rilievi_misure": link.rilievi_misure,
                    "prodotti_fornitore": link.prodotti_fornitore
                })

        result.append({
            "id": progetto.id,
            "upload_id": progetto.upload_id,
            "upload_id_progetto_files": progetto.upload_id_progetto_files,
            "tecnico": progetto.tecnico,
            "stato": progetto.stato,
            "cliente_id": progetto.cliente_id,
            "data_creazione": progetto.data_creazione,
            "importo": progetto.importo,
            "cliente": cliente_dict,
            "fornitori": fornitori_list,
        })

    return result

# Get one
@router.get("/{progetto_id}")
def read_progetto(progetto_id: int, db: Session = Depends(get_db)):
    progetto = db.get(Progetti, progetto_id)
    if not progetto:
        raise HTTPException(status_code=404, detail="Progetto not found")

    # Fetch cliente
    cliente = db.get(Cliente, progetto.cliente_id)
    cliente_dict = {
        "id": cliente.id,
        "upload_id": progetto.upload_id,
        "upload_id_progetto_files": progetto.upload_id_progetto_files,
        "nome_cliente": cliente.nome_cliente,
        "citta": cliente.citta,
        "indirizzo": cliente.indirizzo,
        "numero_tel": cliente.numero_tel,
        "centro_di_costo": cliente.centro_di_costo,
        "contatti": cliente.contatti,
        "note": cliente.note,
        "data_creazione_cliente": cliente.data_creazione,
    } if cliente else {}

    # Fetch linked fornitori
    links = db.exec(
        select(ProgettoFornitoreLink).where(ProgettoFornitoreLink.progetto_id == progetto_id)
    ).all()

    fornitori_data = []
    for link in links:
        fornitore = db.get(Fornitore, link.fornitore_id)
        if fornitore:
            fornitori_data.append({
                "id": fornitore.id,
                "nome_fornitore": fornitore.nome_cliente,
                "indirizzo": fornitore.indirizzo,
                "citta": fornitore.citta,
                "numero_tel": fornitore.numero_tel,
                "sito": fornitore.sito,
                "contatti": fornitore.contatti,
                "data_creazione_fornitore": fornitore.data_creazione,
                "contratti": link.contratti,
                "rilievi_misure": link.rilievi_misure,
                "prodotti_fornitore": link.prodotti_fornitore,
            })

    return {
        "id": progetto.id,
        "tecnico": progetto.tecnico,
        "stato": progetto.stato,
        "cliente_id": progetto.cliente_id,
        "data_creazione": progetto.data_creazione,
        "importo": progetto.importo,
        "cliente": cliente_dict,
        "fornitori": fornitori_data
    }

# Modify one 
@router.put("/{progetto_id}", response_model=ProgettiRead)
def update_progetto(progetto_id: int, progetto_update: ProgettiUpdate, db: Session = Depends(get_db)):
    progetto = db.get(Progetti, progetto_id)
    if not progetto:
        raise HTTPException(status_code=404, detail="Progetto not found")

    # Update base fields
    progetto_data = progetto_update.dict(exclude_unset=True, exclude={"fornitori"})
    for key, value in progetto_data.items():
        setattr(progetto, key, value)
    db.add(progetto)

    # Update fornitori links if provided
    if progetto_update.fornitori is not None:
        # Remove existing links
        existing_links = db.exec(
            select(ProgettoFornitoreLink).where(ProgettoFornitoreLink.progetto_id == progetto_id)
        ).all()
        for link in existing_links:
            db.delete(link)

        # Add new links
        for f in progetto_update.fornitori:
            new_link = ProgettoFornitoreLink(
                progetto_id=progetto_id,
                fornitore_id=f.fornitore_id,
                contratti=[c.model_dump() for c in f.contratti] if f.contratti else [],
                rilievi_misure=[r.model_dump() for r in f.rilievi_misure] if f.rilievi_misure else [],
                prodotti_fornitore=[p.model_dump() for p in f.prodotti_fornitore] if f.prodotti_fornitore else [] 
            )
            db.add(new_link)

    db.commit()
    db.refresh(progetto)
    return progetto