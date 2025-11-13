# Defines API routes and endpoints related to progetti

from fastapi import APIRouter, Depends, HTTPException
import sys
import os
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from sqlalchemy import nulls_last  
from fastapi.responses import ORJSONResponse
import time
#from pprint import pprint

if os.getenv("GITHUB_ACTIONS"): sys.path.append(os.path.dirname(__file__)) 
from models.progetti import Progetti
from models.clienti import Cliente
from models.fornitori import Fornitore
from datetime import datetime, timedelta
from models.progetto_fornitore_link import ProgettoFornitoreLink
from schemas.progetti import ProgettiCreate, ProgettiRead, ProgettiUpdate
from routers.utils import *
from dependecies import get_db

router = APIRouter()

def _fornitore_exists(db: Session, fornitore_id: int) -> bool:
    if not fornitore_id or fornitore_id == 0:
        return False
    return db.exec(select(Fornitore.id).where(Fornitore.id == fornitore_id)).first() is not None


def _replace_fornitori_links(db: Session, progetto_pk: int, fornitori_payload: list):
    # delete existing links
    db.query(ProgettoFornitoreLink).filter(
        ProgettoFornitoreLink.progetto_id == progetto_pk
    ).delete(synchronize_session=False)

    # insert new links
    if fornitori_payload:
        for f in fornitori_payload:
            if not _fornitore_exists(db, f.fornitore_id):
                # skip invalid supplier id
                continue
            link = ProgettoFornitoreLink(
                progetto_id=progetto_pk,
                fornitore_id=f.fornitore_id,
                contratti=[c.model_dump() for c in f.contratti] if f.contratti else [],
                rilievi_misure=[r.model_dump() for r in f.rilievi_misure] if f.rilievi_misure else [],
                prodotti_fornitore=[p.model_dump() for p in f.prodotti_fornitore] if f.prodotti_fornitore else []
            )
            db.add(link)

def create_or_update_progetto(progetto: ProgettiCreate, db: Session) -> Progetti:
    """
    Upsert by progetto.progetto_id:
      - If progetto_id is present and matches an existing row -> UPDATE that row.
      - Else -> CREATE a new Progetti row.
    Also (re)syncs ProgettoFornitoreLink entries for this progetto.
    """

    existing = None
    if progetto.progetto_id:
        existing = db.exec(
            select(Progetti).where(Progetti.progetto_id == progetto.progetto_id)
        ).first()

    # --- SKIP existing projects ---
    if existing:
        return existing

    # --- CREATE path ---
    db_progetto = Progetti(
        progetto_id=progetto.progetto_id,
        tecnico=progetto.tecnico,
        azienda=progetto.azienda,
        centro_di_costo=progetto.centro_di_costo,
        stato=progetto.stato,
        commerciale=progetto.commerciale,
        cliente_id=progetto.cliente_id,
        data_creazione=progetto.data_creazione,
        importo=progetto.importo,
        upload_id=progetto.upload_id,
        upload_id_progetto_files=progetto.upload_id_progetto_files
    )
    db.add(db_progetto)
    db.commit()
    db.refresh(db_progetto)

    # ✅ only add valid fornitori
    _replace_fornitori_links(db, db_progetto.id, progetto.fornitori)

    db.commit()
    db.refresh(db_progetto)
    return db_progetto

# Create
@router.post("", response_model=ProgettiRead)
def create_progetto(progetto: ProgettiCreate, db: Session = Depends(get_db)):
    
    # 1. Create the Progetto record
    db_progetto = Progetti(
        progetto_id=progetto.progetto_id,
        tecnico=progetto.tecnico,
        azienda=progetto.azienda,
        centro_di_costo=progetto.centro_di_costo,
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
    
    payload = fetch_from_gesty("dip-tecnico")
    #pprint(payload)
    
    current_date = datetime.now()
    one_year_ago = current_date - timedelta(days=90)

    payload = [
        project for project in payload
        if project.get("Progetto", {}).get("data_primo_pagamento") and
        datetime.strptime(project["Progetto"]["data_primo_pagamento"], "%Y-%m-%d") >= one_year_ago
    ]

    payload = attach_file_links(payload)
    clienti_inserted_info = create_clienti_from_payload(db, payload)
    progetti_payload = build_progetti_payloads(payload)
    
    
    created_or_updated = []
    for body in progetti_payload:
        progetto_in = ProgettiCreate(**body)
        saved = create_or_update_progetto(progetto_in, db=db)
        created_or_updated.append(saved)
    
    return progetti_payload
    
# Get all
@router.get("")
def read_progetti(db: Session = Depends(get_db)):
    #start_time = time.perf_counter() 
    
    # Eager load cliente and links with their fornitori in one go
    stmt = (
        select(Progetti)
        .options(
            selectinload(Progetti.cliente),
            selectinload(Progetti.fornitori_links).selectinload(ProgettoFornitoreLink.fornitore)
        )
        .order_by(nulls_last(Progetti.data_creazione.desc()))
    )
    progetti = db.exec(stmt).all()

    if not progetti:
        raise HTTPException(status_code=404, detail="No progetti found")

    result = []
    for progetto in progetti:
        cliente = progetto.cliente
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

        fornitori_list = []
        for link in progetto.fornitori_links:
            fornitore = link.fornitore
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
                    "prodotti_fornitore": link.prodotti_fornitore,
                    "note": link.note
                })

        result.append({
            "id": progetto.id,
            "upload_id": progetto.upload_id,
            "upload_id_progetto_files": progetto.upload_id_progetto_files,
            "tecnico": progetto.tecnico,
            "stato": progetto.stato,
            "commerciale": progetto.commerciale,
            "azienda": progetto.azienda,
            "note": progetto.note,
            "centro_di_costo": progetto.centro_di_costo,
            "cliente_id": progetto.cliente_id,
            "data_creazione": progetto.data_creazione,
            "importo": progetto.importo,
            "cliente": cliente_dict,
            "fornitori": fornitori_list,
        })

    #elapsed = time.perf_counter() - start_time      
    return result


ALLOWED_FIELDS = ["note"]
@router.patch("/{progetto_id}/field", response_model=ProgettiRead)
def update_single_progetto_field(
    progetto_id: int,
    field: str,
    value: str | None,
    db: Session = Depends(get_db),
):
    progetto = db.get(Progetti, progetto_id)
    if not progetto:
        raise HTTPException(status_code=404, detail="Progetto not found")

    # ✅ only allow fields in the whitelist
    if field not in ALLOWED_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"Field '{field}' is not allowed to be updated. Allowed fields: {ALLOWED_FIELDS}"
        )

    try:
        setattr(progetto, field, value)
    except AttributeError:
        raise HTTPException(status_code=400, detail=f"Field '{field}' not found on model")

    db.add(progetto)
    db.commit()
    db.refresh(progetto)
    
    return progetto


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
        "commerciale": progetto.commerciale,
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