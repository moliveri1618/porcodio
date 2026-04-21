# Defines API routes and endpoints related to progetti

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    HTTPException,
    Response,
    status,
)
import sys
import os
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload, joinedload, load_only
from sqlalchemy import delete, and_, case, func
from math import ceil
from typing import Optional
# from pprint import pprint


if os.getenv("GITHUB_ACTIONS"):
    sys.path.append(os.path.dirname(__file__))
from models.progetti import Progetti
from models.clienti import Cliente
from models.fornitori import Fornitore
from datetime import datetime, timedelta
from models.progetto_fornitore_link import ProgettoFornitoreLink
from schemas.progetti import ProgettiCreate, ProgettiRead, ProgettiUpdate
from routers.utils import *
from dependecies import get_db
from sqlalchemy import nulls_last

router = APIRouter()


def _fornitore_exists(db: Session, fornitore_id: int) -> bool:
    if not fornitore_id or fornitore_id == 0:
        return False
    return (
        db.exec(select(Fornitore.id).where(Fornitore.id == fornitore_id)).first()
        is not None
    )

def has_any_file(arr):
    return bool(arr) and any((x.file_name or "").strip() for x in arr)

def has_any_file_V2(arr):
    if not arr:
        return False

    for x in arr:
        if isinstance(x, dict):
            if str(x.get("file_name") or "").strip():
                return True
        else:
            if str(getattr(x, "file_name", "") or "").strip():
                return True

    return False

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
                rilievi_misure=(
                    [r.model_dump() for r in f.rilievi_misure]
                    if f.rilievi_misure
                    else []
                ),
                prodotti_fornitore=(
                    [p.model_dump() for p in f.prodotti_fornitore]
                    if f.prodotti_fornitore
                    else []
                ),
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
        data_cambiamento_stato=progetto.data_cambiamento_stato,
        importo=progetto.importo,
        importo_parz=progetto.importo_parz,
        upload_id=progetto.upload_id,
        upload_id_progetto_files=progetto.upload_id_progetto_files,
        status_percent=25,
    )
    db.add(db_progetto)
    db.commit()
    db.refresh(db_progetto)

    # ✅ only add valid fornitori
    _replace_fornitori_links(db, db_progetto.id, progetto.fornitori)

    db.commit()
    db.refresh(db_progetto)
    return db_progetto

def compute_status_percent_db(progetto: Progetti) -> int:
    links = progetto.fornitori_links or []
    n = len(links)

    if n == 0:
        return 25

    total = 25
    contratti_per_link = 50 / n
    rilievi_per_link = 25 / n

    for link in links:
        if link.contratti:
            total += contratti_per_link
        if link.rilievi_misure:
            total += rilievi_per_link

    return max(0, min(100, round(total)))

def compute_status_percent(progetto: ProgettiCreate) -> int:
    fornitori = progetto.fornitori or []
    n = len(fornitori)

    # Project-level = 25 total
    rilievo_done = 1 if (progetto.upload_id or "").strip() else 0
    contratto_done = 1 if (progetto.upload_id_progetto_files or "").strip() else 0
    project_part = (rilievo_done + contratto_done) * 12.5

    if n == 0:
        return max(0, min(100, round(project_part)))

    # Supplier-level
    contratti_per_link = 50 / n
    rilievi_per_link = 25 / n

    total = project_part

    for f in fornitori:
        if has_any_file(f.contratti):
            total += contratti_per_link
        if has_any_file(f.rilievi_misure):
            total += rilievi_per_link

    return max(0, min(100, round(total)))

def compute_status_percent_db_edit(progetto: Progetti) -> int:
    links = progetto.fornitori_links or []
    n = len(links)

    # Project-level = 25 total
    rilievo_done = 1 if (progetto.upload_id or "").strip() else 0
    contratto_done = 1 if (progetto.upload_id_progetto_files or "").strip() else 0
    project_part = (rilievo_done + contratto_done) * 12.5

    if n == 0:
        return max(0, min(100, round(project_part)))

    # Supplier-level
    contratti_per_link = 50 / n
    rilievi_per_link = 25 / n

    total = project_part

    for link in links:
        if has_any_file_V2(link.contratti):
            total += contratti_per_link
        if has_any_file_V2(link.rilievi_misure):
            total += rilievi_per_link

    return max(0, min(100, round(total)))


def format_it(number: float) -> str:
    return f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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
        status_percent=compute_status_percent(progetto),
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
            rilievi_misure=(
                [r.model_dump() for r in f.rilievi_misure] if f.rilievi_misure else []
            ),
            prodotti_fornitore=(
                [p.model_dump() for p in f.prodotti_fornitore]
                if f.prodotti_fornitore
                else []
            ),
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
        project
        for project in payload
        if project.get("Progetto", {}).get("data_primo_pagamento")
        and datetime.strptime(project["Progetto"]["data_primo_pagamento"], "%Y-%m-%d")
        >= one_year_ago
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

@router.get("/sum-importo-parz")
def sum_importo_parz(
    n: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    rows = db.exec(
        select(Progetti.importo_parz)
        .where(func.upper(func.coalesce(Progetti.stato, "")) != "INVIATO")
        .order_by(Progetti.id.asc())
        .limit(n)
    ).all()

    total = sum(x or 0 for x in rows)

    return {
        "n": n,
        "sum_importo_parz": total,
    }


@router.get("/sum-importo-mensile-filtrato")
def sum_importo_filtrato(
    tipo_importo: str = Query("totale", pattern="^(totale|parziale)$"),
    stato: Optional[str] = Query(None),
    data_da: Optional[str] = Query(None),
    data_a: Optional[str] = Query(None),
    tecnico: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    colonna_importo = (
        Progetti.importo_parz
        if tipo_importo.lower() == "parziale"
        else Progetti.importo
    )

    query = select(func.coalesce(func.sum(colonna_importo), 0))
    conditions = []

    # tecnico
    if tecnico and tecnico.strip() and tecnico.lower() != "generali":
        conditions.append(Progetti.tecnico == tecnico.strip())

    # stato
    if stato and stato.strip():
        stato_clean = stato.strip().upper()

        if stato_clean == "VAL+INV":
            conditions.append(Progetti.stato.in_(["VALIDATO", "INVIATO"]))
        else:
            conditions.append(Progetti.stato == stato_clean)

    # date
    if data_da:
        conditions.append(Progetti.data_cambiamento_stato >= f"{data_da}T00:00:00.000Z")

    if data_a:
        conditions.append(Progetti.data_cambiamento_stato <= f"{data_a}T23:59:59.999Z")

    query = query.where(*conditions)

    totale = db.exec(query).first()
    return totale


@router.get("/pdf-progetti-filtrati")
def get_progetti_filtrati(
    tipo_importo: str = Query("totale", pattern="^(totale|parziale)$"),
    stato: Optional[str] = Query(None),
    data_da: Optional[str] = Query(None),
    data_a: Optional[str] = Query(None),
    tecnico: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    colonna_importo = (
        Progetti.importo_parz
        if tipo_importo.lower() == "parziale"
        else Progetti.importo
    )

    conditions = []

    # tecnico
    if tecnico and tecnico.strip() and tecnico.lower() != "generali":
        conditions.append(Progetti.tecnico == tecnico.strip())

    # stato
    if stato and stato.strip():
        stato_clean = stato.strip().upper()

        if stato_clean == "VAL+INV":
            conditions.append(Progetti.stato.in_(["VALIDATO", "INVIATO"]))
        else:
            conditions.append(Progetti.stato == stato_clean)

    # date
    if data_da:
        conditions.append(Progetti.data_cambiamento >= f"{data_da}T00:00:00.000Z")

    if data_a:
        conditions.append(Progetti.data_cambiamento <= f"{data_a}T23:59:59.999Z")

    query = (
        select(Progetti).where(*conditions).order_by(Progetti.data_cambiamento.desc())
    )

    righe = db.exec(query).all()

    return {
        "tipo_importo": tipo_importo,
        "count": len(righe),
        "totale_importo_filtrato": sum(
            float(
                getattr(r, "importo_parz" if tipo_importo == "parziale" else "importo")
                or 0
            )
            for r in righe
        ),
        "rows": righe,
    }


# actually v2
@router.get("/v5")
def read_progettiV5(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    include_completed: bool = False,
    include_suspended: bool = False,
    tecnico: str | None = None,
):
    # ------------------------------------------------------------
    # 1) Compute pagination offset once
    # ------------------------------------------------------------
    offset = (page - 1) * page_size

    # ------------------------------------------------------------
    # 2) Custom priority for sorting "stato"
    #    Lower number = comes first
    # ------------------------------------------------------------
    stato_priority = case(
        (func.upper(func.coalesce(Progetti.stato, "")) == "VALIDATO", 1),
        (func.upper(func.coalesce(Progetti.stato, "")) == "INVIATO", 2),
        (func.upper(func.coalesce(Progetti.stato, "")).in_(["ATTIVO", "SOSPESO"]), 3),
        else_=999,
    )

    # ------------------------------------------------------------
    # 3) Define SQL expression for "completed"
    #    This lets DB filter it directly instead of Python doing it
    # ------------------------------------------------------------
    is_completed_expr = and_(
        func.coalesce(Progetti.status_percent, 0) == 100,
        func.upper(func.coalesce(Progetti.stato, "")) == "VALIDATO",
    )

    # ------------------------------------------------------------
    # 4) Build all WHERE filters once
    # ------------------------------------------------------------
    filters = []

    # Filter by tecnico unless it is empty or "generali"
    if tecnico and tecnico.strip().lower() != "generali":
        tecnico_value = tecnico.strip()
        filters.append(Progetti.tecnico.ilike(f"%{tecnico_value}%"))

    # Exclude suspended unless explicitly included
    if not include_suspended:
        filters.append(func.upper(func.coalesce(Progetti.stato, "")) != "SOSPESO")

    # Exclude completed unless explicitly included
    if not include_completed:
        filters.append(~is_completed_expr)

    # ------------------------------------------------------------
    # 5) Count query:
    #    count ONLY rows that match the real filters
    # ------------------------------------------------------------
    total_stmt = select(func.count()).select_from(Progetti)
    if filters:
        total_stmt = total_stmt.where(*filters)

    total = db.exec(total_stmt).one()

    # Early return if nothing found
    if total == 0:
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
        }

    # ------------------------------------------------------------
    # 6) Main query:
    #    IMPORTANT: apply filters + order + offset + limit in SQL
    #    so database returns only the requested page
    # ------------------------------------------------------------
    stmt = (
        select(Progetti)
        .where(*filters)
        .options(
            # Load related client in one extra query, not N queries
            selectinload(Progetti.cliente),
            # Load supplier links and linked supplier data efficiently
            selectinload(Progetti.fornitori_links).selectinload(
                ProgettoFornitoreLink.fornitore
            ),
        )
        .order_by(
            stato_priority.asc(),
            Progetti.data_creazione.asc().nullslast(),
        )
        .offset(offset)
        .limit(page_size)
    )

    progetti = db.exec(stmt).all()

    # ------------------------------------------------------------
    # 7) Build API response only for current page rows
    # ------------------------------------------------------------
    items = []

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
            if not fornitore:
                continue

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

        status_percent = int(progetto.status_percent or 0)
        is_completed = (
            status_percent == 100
            and str(progetto.stato or "").strip().upper() == "VALIDATO"
        )

        items.append(
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

    # ------------------------------------------------------------
    # 8) Return already-paginated data
    # ------------------------------------------------------------
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size),
    }


@router.get("/v3")
def read_progettiV3(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    include_completed: bool = False,
    include_suspended: bool = False,
    tecnico: str | None = None,
):
    offset = (page - 1) * page_size

    stato_priority = case(
        (func.upper(func.coalesce(Progetti.stato, "")) == "VALIDATO", 1),
        (func.upper(func.coalesce(Progetti.stato, "")) == "INVIATO", 2),
        (func.upper(func.coalesce(Progetti.stato, "")).in_(["ATTIVO", "SOSPESO"]), 3),
        else_=999,
    )

    is_completed_expr = and_(
        func.coalesce(Progetti.status_percent, 0) == 100,
        func.upper(func.coalesce(Progetti.stato, "")) == "VALIDATO",
    )

    filters: list = []
    if tecnico and tecnico.strip().lower() != "generali":
        filters.append(Progetti.tecnico.ilike(f"%{tecnico.strip()}%"))
    if not include_suspended:
        filters.append(func.upper(func.coalesce(Progetti.stato, "")) != "SOSPESO")
    if not include_completed:
        filters.append(~is_completed_expr)

    total = db.exec(select(func.count()).select_from(Progetti).where(*filters)).one()
    if total == 0:
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
        }

    stmt = (
        select(Progetti)
        .where(*filters)
        .options(
            selectinload(Progetti.cliente),
            selectinload(Progetti.fornitori_links).selectinload(
                ProgettoFornitoreLink.fornitore
            ),
        )
        .order_by(stato_priority.asc(), Progetti.data_creazione.asc().nullslast())
        .offset(offset)
        .limit(page_size)
    )
    progetti = db.exec(stmt).all()

    def _p_dict(p: Progetti) -> dict:
        c = p.cliente
        cliente_dict = (
            {
                "id": c.id,
                "nome_cliente": c.nome_cliente,
                "citta": c.citta,
                "indirizzo": c.indirizzo,
                "numero_tel": c.numero_tel,
                "centro_di_costo": c.centro_di_costo,
                "contatti": c.contatti,
                "note": c.note,
                "data_creazione_cliente": c.data_creazione,
            }
            if c
            else {}
        )

        fornitori_list = [
            {
                "id": f.fornitore.id,
                "nome_fornitore": f.fornitore.nome_cliente,
                "indirizzo": f.fornitore.indirizzo,
                "citta": f.fornitore.citta,
                "numero_tel": f.fornitore.numero_tel,
                "sito": f.fornitore.sito,
                "contatti": f.fornitore.contatti,
                "data_creazione_fornitore": f.fornitore.data_creazione,
                "contratti": f.contratti,
                "rilievi_misure": f.rilievi_misure,
                "prodotti_fornitore": f.prodotti_fornitore,
                "note": f.note,
            }
            for f in p.fornitori_links
            if f.fornitore
        ]

        status_percent = int(p.status_percent or 0)
        is_completed = (
            status_percent == 100 and str(p.stato or "").strip().upper() == "VALIDATO"
        )

        return {
            "id": p.id,
            "upload_id": p.upload_id,
            "upload_id_progetto_files": p.upload_id_progetto_files,
            "tecnico": p.tecnico,
            "stato": p.stato,
            "commerciale": p.commerciale,
            "azienda": p.azienda,
            "note": p.note,
            "centro_di_costo": p.centro_di_costo,
            "cliente_id": p.cliente_id,
            "data_cambiamento_stato": p.data_cambiamento_stato,
            "data_creazione": p.data_creazione,
            "importo": p.importo,
            "importo_parz": p.importo_parz,
            "cliente": cliente_dict,
            "fornitori": fornitori_list,
            "status_percent": status_percent,
            "is_completed": is_completed,
        }

    items = [_p_dict(p) for p in progetti]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/v4")
def read_progettiV4(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    include_completed: bool = False,
    include_suspended: bool = False,
    tecnico: str | None = None,
):
    offset = (page - 1) * page_size

    stato_upper = func.upper(func.coalesce(Progetti.stato, ""))

    stato_priority = case(
        (stato_upper == "VALIDATO", 1),
        (stato_upper == "INVIATO", 2),
        (stato_upper.in_(["ATTIVO", "SOSPESO"]), 3),
        else_=999,
    )

    is_completed_expr = and_(
        func.coalesce(Progetti.status_percent, 0) == 100,
        stato_upper == "VALIDATO",
    )

    filters = []

    if tecnico and tecnico.strip().lower() != "generali":
        filters.append(Progetti.tecnico.ilike(f"%{tecnico.strip()}%"))

    if not include_suspended:
        filters.append(stato_upper != "SOSPESO")

    if not include_completed:
        filters.append(~is_completed_expr)

    # FAST COUNT
    total_stmt = select(func.count(Progetti.id))
    if filters:
        total_stmt = total_stmt.where(*filters)

    total = db.exec(total_stmt).one()

    if total == 0:
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
        }

    stmt = (
        select(Progetti)
        .where(*filters)
        .options(
            # Only columns needed from Progetti
            load_only(
                Progetti.id,
                Progetti.upload_id,
                Progetti.upload_id_progetto_files,
                Progetti.tecnico,
                Progetti.stato,
                Progetti.commerciale,
                Progetti.azienda,
                Progetti.note,
                Progetti.centro_di_costo,
                Progetti.cliente_id,
                Progetti.data_cambiamento_stato,
                Progetti.data_creazione,
                Progetti.importo,
                Progetti.importo_parz,
                Progetti.status_percent,
            ),
            # cliente (1-to-1 → joinedload faster)
            joinedload(Progetti.cliente).load_only(
                Cliente.id,
                Cliente.nome_cliente,
                Cliente.citta,
                Cliente.indirizzo,
                Cliente.numero_tel,
                Cliente.centro_di_costo,
                Cliente.contatti,
                Cliente.note,
                Cliente.data_creazione,
            ),
            # fornitori
            selectinload(Progetti.fornitori_links)
            .selectinload(ProgettoFornitoreLink.fornitore)
            .load_only(
                Fornitore.id,
                Fornitore.nome_cliente,
                Fornitore.indirizzo,
                Fornitore.citta,
                Fornitore.numero_tel,
                Fornitore.sito,
                Fornitore.contatti,
                Fornitore.data_creazione,
            ),
        )
        .order_by(
            stato_priority.asc(),
            Progetti.data_creazione.asc().nullslast(),
        )
        .offset(offset)
        .limit(page_size)
    )

    progetti = db.exec(stmt).all()

    items = []

    for p in progetti:

        cliente = p.cliente
        cliente_dict = None

        if cliente:
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
            }

        fornitori = []

        for f in p.fornitori_links:
            if not f.fornitore:
                continue

            prodotti = f.prodotti_fornitore or []

            display_prodotti = (
                ", ".join(f"{prod['nome']} ({prod['quantita']})" for prod in prodotti)
                if prodotti
                else "—"
            )

            fornitori.append(
                {
                    "id": f.fornitore.id,
                    "nome_fornitore": f.fornitore.nome_cliente,
                    "indirizzo": f.fornitore.indirizzo,
                    "citta": f.fornitore.citta,
                    "numero_tel": f.fornitore.numero_tel,
                    "sito": f.fornitore.sito,
                    "contatti": f.fornitore.contatti,
                    "data_creazione_fornitore": f.fornitore.data_creazione,
                    "contratti": f.contratti,
                    "rilievi_misure": f.rilievi_misure,
                    "prodotti_fornitore": prodotti,
                    "display_prodotti": display_prodotti,
                    "note": f.note,
                }
            )

        supplier_names = ", ".join(f["nome_fornitore"] for f in fornitori)

        # formatting helpers
        display_date = p.data_creazione.strftime("%d %b %Y") if p.data_creazione else ""

        display_importo = (
            f"{p.importo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            if p.importo is not None
            else "0,00"
        )

        display_importo_parz = (
            f"{p.importo_parz:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
            if p.importo_parz is not None
            else "0,00"
        )

        status_percent = int(p.status_percent or 0)
        is_completed = status_percent == 100 and (p.stato or "").upper() == "VALIDATO"

        items.append(
            {
                "id": p.id,
                "upload_id": p.upload_id,
                "upload_id_progetto_files": p.upload_id_progetto_files,
                "tecnico": p.tecnico,
                "stato": p.stato,
                "commerciale": p.commerciale,
                "azienda": p.azienda,
                "note": p.note,
                "centro_di_costo": p.centro_di_costo,
                "cliente_id": p.cliente_id,
                "data_cambiamento_stato": p.data_cambiamento_stato,
                "data_creazione": p.data_creazione,
                "importo": p.importo,
                "importo_parz": p.importo_parz,
                # NEW DISPLAY FIELDS
                "display_date": display_date,
                "display_importo": display_importo,
                "display_importo_parz": display_importo_parz,
                "supplier_names": supplier_names,
                "cliente": cliente_dict,
                "fornitori": fornitori,
                "status_percent": status_percent,
                "is_completed": is_completed,
            }
        )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size),
    }


@router.get("/v2")
def read_progettiV2(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    include_completed: bool = False,
    include_suspended: bool = False,
    tecnico: str | None = None,
    cliente_nome: str | None = None,
    sort_tecnico: bool = False,  
):
    offset = (page - 1) * page_size

    stato_upper = func.upper(func.coalesce(Progetti.stato, ""))

    stato_priority = case(
        (stato_upper == "VALIDATO", 1),
        (stato_upper == "INVIATO", 2),
        (stato_upper == "ATTESA", 3),
        (stato_upper.in_(["ATTIVO", "SOSPESO"]), 4),
        else_=999,
    )

    is_completed_expr = and_(
        func.coalesce(Progetti.status_percent, 0) == 100,
        stato_upper == "VALIDATO",
    )

    filters = []
    if tecnico and tecnico.strip().lower() != "generali":
        filters.append(Progetti.tecnico.ilike(f"%{tecnico.strip()}%"))
    if not include_suspended:
        filters.append(stato_upper != "SOSPESO")
    if not include_completed:
        filters.append(~is_completed_expr)
    if cliente_nome and cliente_nome.strip():
        filters.append(Cliente.nome_cliente.ilike(f"%{cliente_nome.strip()}%"))

    total = db.exec(
        select(func.count(Progetti.id))
        .select_from(Progetti)
        .join(Cliente, Progetti.cliente_id == Cliente.id)
        .where(*filters)
    ).one()
    if total == 0:
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
        }

    if sort_tecnico:
        tecnico_empty_first = case(
            (
                func.trim(func.coalesce(Progetti.tecnico, "")) == "",
                0,
            ),
            else_=1,
        )

        order_by_clause = [
            tecnico_empty_first.asc(),                  # empty/null first
            func.lower(func.coalesce(Progetti.tecnico, "")).asc(),  # alphabetical
            Progetti.data_creazione.asc().nullslast(),  # tie-breaker
        ]
    else:
        order_by_clause = [
            stato_priority.asc(),
            Progetti.data_creazione.asc().nullslast(),
        ]

    stmt = (
        select(Progetti)
        .join(Cliente, Progetti.cliente_id == Cliente.id)
        .where(*filters)
        .options(
            load_only(
                Progetti.id,
                Progetti.progetto_id,
                Progetti.upload_id,
                Progetti.upload_id_progetto_files,
                Progetti.tecnico,
                Progetti.stato,
                Progetti.commerciale,
                Progetti.azienda,
                Progetti.note,
                Progetti.centro_di_costo,
                Progetti.cliente_id,
                Progetti.data_cambiamento_stato,
                Progetti.data_creazione,
                Progetti.importo,
                Progetti.importo_parz,
                Progetti.status_percent,
            ),
            joinedload(Progetti.cliente).load_only(
                Cliente.id,
                Cliente.nome_cliente,
                Cliente.citta,
                Cliente.indirizzo,
                Cliente.numero_tel,
                Cliente.centro_di_costo,
                Cliente.contatti,
                Cliente.note,
                Cliente.data_creazione,
            ),
            selectinload(Progetti.fornitori_links)
            .selectinload(ProgettoFornitoreLink.fornitore)
            .load_only(
                Fornitore.id,
                Fornitore.nome_cliente,
                Fornitore.indirizzo,
                Fornitore.citta,
                Fornitore.numero_tel,
                Fornitore.sito,
                Fornitore.contatti,
                Fornitore.data_creazione,
            ),
        )
        .order_by(*order_by_clause)
        .offset(offset)
        .limit(page_size)
    )

    progetti = db.exec(stmt).all()

    def _format_currency(val) -> str:
        return (
            f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            if val is not None
            else "0,00"
        )

    items = []
    for p in progetti:
        c = p.cliente
        cliente_dict = (
            {
                "id": c.id,
                "nome_cliente": c.nome_cliente,
                "citta": c.citta,
                "indirizzo": c.indirizzo,
                "numero_tel": c.numero_tel,
                "centro_di_costo": c.centro_di_costo,
                "contatti": c.contatti,
                "note": c.note,
                "data_creazione_cliente": c.data_creazione,
            }
            if c
            else None
        )

        stato_upper_val = (p.stato or "").upper()
        status_percent = int(p.status_percent or 0)

        fornitori = [
            {
                "id": f.fornitore.id,
                "nome_fornitore": f.fornitore.nome_cliente,
                "indirizzo": f.fornitore.indirizzo,
                "citta": f.fornitore.citta,
                "numero_tel": f.fornitore.numero_tel,
                "sito": f.fornitore.sito,
                "contatti": f.fornitore.contatti,
                "data_creazione_fornitore": f.fornitore.data_creazione,
                "contratti": f.contratti,
                "rilievi_misure": f.rilievi_misure,
                "prodotti_fornitore": f.prodotti_fornitore or [],
                "display_prodotti": ", ".join(
                    f"{prod['nome']} ({prod['quantita']})"
                    for prod in (f.prodotti_fornitore or [])
                )
                or "—",
                "note": f.note,
            }
            for f in p.fornitori_links
            if f.fornitore
        ]

        items.append(
            {
                "id": p.id,
                "progetto": p.progetto_id,
                "upload_id": p.upload_id,
                "upload_id_progetto_files": p.upload_id_progetto_files,
                "tecnico": p.tecnico,
                "stato": p.stato,
                "commerciale": p.commerciale,
                "azienda": p.azienda,
                "note": p.note,
                "centro_di_costo": p.centro_di_costo,
                "cliente_id": p.cliente_id,
                "data_cambiamento_stato": p.data_cambiamento_stato,
                "data_creazione": p.data_creazione,
                "importo": p.importo,
                "importo_parz": p.importo_parz,
                "display_date": (
                    p.data_creazione.strftime("%d %b %Y") if p.data_creazione else ""
                ),
                "display_importo": _format_currency(p.importo),
                "display_importo_parz": _format_currency(p.importo_parz),
                "supplier_names": ", ".join(f["nome_fornitore"] for f in fornitori),
                "cliente": cliente_dict,
                "fornitori": fornitori,
                "status_percent": status_percent,
                "is_completed": status_percent == 100 and stato_upper_val == "VALIDATO",
            }
        )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


ALLOWED_FIELDS = ["note", "data_cambiamento_stato"]  # DO NOT CHANGE


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
            detail=f"Field '{field}' is not allowed to be updated. Allowed fields: {ALLOWED_FIELDS}",
        )

    try:
        setattr(progetto, field, value)
    except AttributeError:
        raise HTTPException(
            status_code=400, detail=f"Field '{field}' not found on model"
        )

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
    cliente_dict = (
        {
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
        }
        if cliente
        else {}
    )

    # Fetch linked fornitori
    links = db.exec(
        select(ProgettoFornitoreLink).where(
            ProgettoFornitoreLink.progetto_id == progetto_id
        )
    ).all()

    fornitori_data = []
    for link in links:
        fornitore = db.get(Fornitore, link.fornitore_id)
        if fornitore:
            fornitori_data.append(
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
                }
            )

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
        "fornitori": fornitori_data,
    }


# Modify one
@router.put("/{progetto_id}", response_model=ProgettiRead)
def update_progetto(
    progetto_id: int, progetto_update: ProgettiUpdate, db: Session = Depends(get_db)
):
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
            select(ProgettoFornitoreLink).where(
                ProgettoFornitoreLink.progetto_id == progetto_id
            )
        ).all()
        for link in existing_links:
            db.delete(link)

        # Add new links
        for f in progetto_update.fornitori:
            new_link = ProgettoFornitoreLink(
                progetto_id=progetto_id,
                fornitore_id=f.fornitore_id,
                contratti=[c.model_dump() for c in f.contratti] if f.contratti else [],
                rilievi_misure=(
                    [r.model_dump() for r in f.rilievi_misure]
                    if f.rilievi_misure
                    else []
                ),
                prodotti_fornitore=(
                    [p.model_dump() for p in f.prodotti_fornitore]
                    if f.prodotti_fornitore
                    else []
                ),
            )
            db.add(new_link)

    db.flush()
    db.refresh(progetto)

    progetto = db.exec(
        select(Progetti)
        .where(Progetti.id == progetto_id)
        .options(selectinload(Progetti.fornitori_links))
    ).first()

    progetto.status_percent = compute_status_percent_db_edit(progetto)
    db.add(progetto)

    db.commit()
    db.refresh(progetto)

    return progetto


# Delete one
@router.delete("/v1/{progetto_id}")
def delete_progetto(progetto_id: int, db: Session = Depends(get_db)):
    progetto = db.get(Progetti, progetto_id)
    if not progetto:
        raise HTTPException(status_code=404, detail="Progetto not found")

    # Bulk delete associated links
    db.exec(
        delete(ProgettoFornitoreLink).where(
            ProgettoFornitoreLink.progetto_id == progetto_id
        )
    )

    # Delete the progetto
    db.delete(progetto)
    db.commit()

    return {"message": f"Progetto {progetto_id} deleted successfully"}


# Delete one
@router.delete("/v2/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_progetto(
    project_id: int,
    db: Session = Depends(get_db),
):

    try:
        # Optional existence check
        exists = db.exec(select(Progetti.id).where(Progetti.id == project_id)).first()

        if not exists:
            raise HTTPException(status_code=404, detail="Project not found")

        # 1) delete link rows first
        db.execute(
            delete(ProgettoFornitoreLink).where(
                ProgettoFornitoreLink.progetto_id == project_id
            )
        )

        # 2) delete project
        result = db.execute(delete(Progetti).where(Progetti.id == project_id))

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Project not found")

        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


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


@router.post("/recalc_status_percent")
def recalc_status_percent(db: Session = Depends(get_db)):
    stmt = select(Progetti).options(selectinload(Progetti.fornitori_links))
    progetti = db.exec(stmt).all()

    if not progetti:
        raise HTTPException(status_code=404, detail="No progetti found")

    updated = 0

    for p in progetti:
        new_status_percent = compute_status_percent_db(p)

        if (p.status_percent or 0) != new_status_percent:
            p.status_percent = new_status_percent
            db.add(p)
            updated += 1

    db.commit()

    return {
        "total": len(progetti),
        "updated": updated,
    }

@router.post("/recalc_status_percent/{project_id}")
def recalc_status_percent_one(project_id: int, db: Session = Depends(get_db)):
    stmt = (
        select(Progetti)
        .where(Progetti.id == project_id)
        .options(selectinload(Progetti.fornitori_links))
    )

    progetto = db.exec(stmt).first()

    if not progetto:
        raise HTTPException(status_code=404, detail="Project not found")

    new_status_percent = compute_status_percent_db(progetto)

    updated = False
    if (progetto.status_percent or 0) != new_status_percent:
        progetto.status_percent = new_status_percent
        updated = True

    db.commit()

    return {
        "project_id": project_id,
        "status_percent": new_status_percent,
        "updated": updated,
    }
