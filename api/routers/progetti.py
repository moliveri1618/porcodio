# Defines API routes and endpoints related to progetti

from fastapi import APIRouter, Depends, HTTPException, Query
import sys
import os
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, case, nulls_last
from fastapi.responses import ORJSONResponse
import time
from math import ceil
# from pprint import pprint

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


def has_any_file(arr):
    return bool(arr) and any((x.file_name or "").strip() for x in arr)


def compute_status_percent(progetto: ProgettiCreate) -> int:
    fornitori = progetto.fornitori or []
    n = len(fornitori)

    # Project-level
    rilievo_done = 1 if (progetto.upload_id or "").strip() else 0
    contratto_done = 1 if (progetto.upload_id_progetto_files or "").strip() else 0
    project_part = (rilievo_done + contratto_done) * 12.5

    # Supplier-level
    orders_done = sum(1 for f in fornitori if has_any_file(f.contratti))
    ordini_part = (orders_done / n) * 50 if n > 0 else 0

    conferme_done = sum(1 for f in fornitori if has_any_file(f.rilievi_misure))
    conferme_part = (conferme_done / n) * 25 if n > 0 else 0

    total = project_part + ordini_part + conferme_part
    return max(0, min(100, round(total)))


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
        return None

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
        importo_parz=progetto.importo_parz,
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

    # --- compute importo_parz server-side ---
    cdc = (progetto.centro_di_costo or "").strip().lower()
    aliquota = 0.042 if cdc == "genova" else 0.025
    calc_importo_parz = (progetto.importo or 0.0) * aliquota
    
    # 1. Create the Progetto record
    db_progetto = Progetti(
        progetto_id=progetto.progetto_id,
        tecnico=progetto.tecnico,
        azienda=progetto.azienda,
        centro_di_costo=progetto.centro_di_costo,
        stato=progetto.stato,
        data_cambiamento_stato=progetto.data_cambiamento_stato,
        cliente_id=progetto.cliente_id,
        data_creazione=progetto.data_creazione,
        importo=progetto.importo,
        importo_parz=calc_importo_parz,
        upload_id=progetto.upload_id,
        upload_id_progetto_files=progetto.upload_id_progetto_files,
        status_percent = compute_status_percent(progetto)
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
    # pprint(payload)

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

    created = []
    for body in progetti_payload:
        progetto_in = ProgettiCreate(**body)
        saved = create_or_update_progetto(progetto_in, db=db)
        if saved is not None:
            created.append(saved)

    return created


# Get all
@router.get("")
def read_progetti(db: Session = Depends(get_db)):
    # start_time = time.perf_counter()

    # Eager load cliente and links with their fornitori in one go
    stmt = (
        select(Progetti)
        .options(
            selectinload(Progetti.cliente),
            selectinload(Progetti.fornitori_links).selectinload(
                ProgettoFornitoreLink.fornitore
            ),
        )
        .order_by(nulls_last(Progetti.data_creazione.desc()))
        # .limit(25)
    )
    progetti = db.exec(stmt).all()

    if not progetti:
        raise HTTPException(status_code=404, detail="No progetti found")

    result = []
    for progetto in progetti:
        cliente = progetto.cliente
        cliente_dict = (
            {
                "id": cliente.id,
                "nome_cliente": cliente.nome_cliente,
                "citta": cliente.citta,
                "indirizzo": cliente.indirizzo,
                "numero_tel": cliente.numero_tel,
                "centro_di_costo": cliente.centro_di_costo,
                "contatti": cliente.contatti,
                "note": cliente.note,
                "data_creazione_cliente": cliente.data_creazione,
            }
            if cliente
            else {}
        )

        fornitori_list = []
        for link in progetto.fornitori_links:
            fornitore = link.fornitore
            if fornitore:
                fornitori_list.append(
                    {
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
                        "note": link.note,
                    }
                )

        result.append(
            {
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
                "data_cambiamento_stato": progetto.data_cambiamento_stato,
                "data_creazione": progetto.data_creazione,
                "importo": progetto.importo,
                "importo_parz": progetto.importo_parz,
                "cliente": cliente_dict,
                "fornitori": fornitori_list,
            }
        )

    # elapsed = time.perf_counter() - start_time
    return result


# Get all
@router.get("/v2")
def read_progettiV2(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    include_completed: bool = False,
    include_suspended: bool = False,
    tecnico: str | None = None
):

    # separate count query
    offset = (page - 1) * page_size
    total_stmt = select(func.count()).select_from(Progetti)
    total = db.exec(total_stmt).one()
    if total == 0:
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
        }

    # sorting
    stato_priority = case(
        (func.upper(Progetti.stato) == "VALIDATO", 1),
        (func.upper(Progetti.stato) == "INVIATO", 2),
        (func.upper(Progetti.stato).in_(["ATTIVO", "SOSPESO"]), 3),
        else_=999,
    )

    # base query
    stmt = select(Progetti).options(
        selectinload(Progetti.cliente),
        selectinload(Progetti.fornitori_links).selectinload(
            ProgettoFornitoreLink.fornitore
        ),
    )

    # filtro tecnico
    if tecnico and tecnico.strip().lower() != "generali":
        stmt = stmt.where(
            func.lower(func.coalesce(Progetti.tecnico, "")).contains(
                tecnico.strip().lower()
            )
        )

    # filtro sospesi
    if not include_suspended:
        stmt = stmt.where(func.upper(func.coalesce(Progetti.stato, "")) != "SOSPESO")

    # sorting
    stmt = stmt.order_by(
        stato_priority.asc(),
        Progetti.data_creazione.asc().nullslast(),
    )
    progetti = db.exec(stmt).all()

    result = []
    for progetto in progetti:
        cliente = progetto.cliente
        cliente_dict = (
            {
                "id": cliente.id,
                "nome_cliente": cliente.nome_cliente,
                "citta": cliente.citta,
                "indirizzo": cliente.indirizzo,
                "numero_tel": cliente.numero_tel,
                "centro_di_costo": cliente.centro_di_costo,
                "contatti": cliente.contatti,
                "note": cliente.note,
                "data_creazione_cliente": cliente.data_creazione,
            }
            if cliente
            else {}
        )

        fornitori_list = []
        for link in progetto.fornitori_links:
            fornitore = link.fornitore
            if fornitore:
                fornitori_list.append(
                    {
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
                        "note": link.note,
                    }
                )

        # completed logic
        n = len(fornitori_list)

        rilievo_done = (
            1 if (progetto.upload_id and str(progetto.upload_id).strip()) else 0
        )
        contratto_done = (
            1
            if (
                progetto.upload_id_progetto_files
                and str(progetto.upload_id_progetto_files).strip()
            )
            else 0
        )
        project_part = (rilievo_done + contratto_done) * 12.5

        orders_done = sum(
            1
            for f in fornitori_list
            if isinstance(f.get("contratti"), list)
            and any(
                c.get("file_name") and str(c["file_name"]).strip()
                for c in f["contratti"]
            )
        )
        ordini_part = (orders_done / n) * 50 if n > 0 else 0

        conferme_done = sum(
            1
            for f in fornitori_list
            if isinstance(f.get("rilievi_misure"), list)
            and any(
                r.get("file_name") and str(r["file_name"]).strip()
                for r in f["rilievi_misure"]
            )
        )
        conferme_part = (conferme_done / n) * 25 if n > 0 else 0

        status_percent = max(
            0,
            min(100, round(project_part + ordini_part + conferme_part)),
        )

        is_completed = (
            status_percent == 100
            and str(progetto.stato or "").strip().upper() == "VALIDATO"
        )

        result.append(
            {
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
                "data_cambiamento_stato": progetto.data_cambiamento_stato,
                "data_creazione": progetto.data_creazione,
                "importo": progetto.importo,
                "importo_parz": progetto.importo_parz,
                "cliente": cliente_dict,
                "fornitori": fornitori_list,
                "status_percent": status_percent,
                "is_completed": is_completed,
            }
        )

    # filter completed
    if not include_completed:
        result = [item for item in result if not item["is_completed"]]

    # paginate AFTER filters
    total = len(result)
    offset = (page - 1) * page_size
    paged_result = result[offset : offset + page_size]

    return {
            "items": result,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": ceil(total / page_size),
        }


ALLOWED_FIELDS = ["note", "data_cambiamento_stato"] # DO NOT CHANGE
@router.put("/{progetto_id}/field", response_model=ProgettiRead)
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
        "data_cambiamento_stato": progetto.data_cambiamento_stato,
        "commerciale": progetto.commerciale,
        "cliente_id": progetto.cliente_id,
        "data_creazione": progetto.data_creazione,
        "importo": progetto.importo,
        "importo_parz": progetto.importo_parz,
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


@router.post("/recalc_importo_parz")
def recalc_importo_parz(db: Session = Depends(get_db)):
    # Fetch all progetti
    progetti = db.exec(select(Progetti)).all()
    if not progetti:
        raise HTTPException(status_code=404, detail="No progetti found")

    updated = 0
    details = []

    for p in progetti:
        cdc = (p.centro_di_costo or "").strip().lower()
        aliquota = 0.042 if cdc == "genova" else 0.025
        new_importo_parz = (p.importo or 0.0) * aliquota

        old_importo_parz = p.importo_parz or 0.0

        # update only if changed (tolerance avoids float noise)
        if abs(old_importo_parz - new_importo_parz) > 1e-9:
            p.importo_parz = new_importo_parz
            db.add(p)
            updated += 1

        details.append({
            "id": p.id,
            "centro_di_costo": p.centro_di_costo,
            "importo": p.importo,
            "old_importo_parz": old_importo_parz,
            "new_importo_parz": new_importo_parz,
            "changed": abs(old_importo_parz - new_importo_parz) > 1e-9,
        })

    db.commit()

    return {
        "total": len(progetti),
        "updated": updated,
        "details": details,
    }
