# utils/gesty.py

import httpx
from fastapi import HTTPException
import sys
import os
from datetime import datetime, timezone
from typing import List, Dict, Any

if os.getenv("GITHUB_ACTIONS"): sys.path.append(os.path.dirname(__file__)) 
from models.progetti import Progetti
from models.clienti import Cliente
from models.fornitori import Fornitore
from models.prodotti import Prodotto
from models.progetto_fornitore_link import ProgettoFornitoreLink
from schemas.progetti import ProgettiCreate, ProgettiRead, ProgettiUpdate
from routers.utils import *
from dependecies import get_db
from sqlmodel import Session, select
from sqlalchemy import and_, func, or_

API_BASE = "https://www.tigulliocrm.it/api"
API_KEY = "xAe5xrokrKL4g7sbyGHQ3mZ9wyqUVks7"
BASE_URL = "https://fsvejdikpdhubuz3kxl7w3koiq0iyvyj.lambda-url.eu-north-1.on.aws".rstrip("/")


from typing import Literal

POINTING_SPEC_WEIGHTS = {
    "falegnameria": 0.10,
    "accessori_avvolgibile": 0.15,
    "accessori_porta_blindata": 0.10,
    "avvolgibile": 0.20,
    "zanzariera": 0.20,
    "motori": 0.20,
    "cassonetto": 0.25,
    "persiana": 0.30,
    "grata": 0.35,
    "porta_interna": 0.50,
    "infisso": 0.55,
    "porta_blindata": 4.50,
}

POINTING_SERVICE_PRODUCTS = {
    "assistenza_programmata",
    "servizi_accessori",
    "estensione_garanzia",
    "servizio",
    "altro",
}

POINTING_FORM_VALUE_TO_SPEC = {
    "infisso": "infisso",
    "infisso_antirumore": "infisso",
    "finestre": "infisso",
    "avvolgibile": "avvolgibile",
    "avvolgibili": "avvolgibile",
    "avvolgibile_teknika": "avvolgibile",
    "tende": "avvolgibile",
    "tende_tecniche": "avvolgibile",
    "cassettoni": "cassonetto",
    "zanzariere": "zanzariera",
    "persiane": "persiana",
    "fermapersiana": "persiana",
    "grate_di_sicurezza": "grata",
    "porte_blindate": "porta_blindata",
    "blindato": "porta_blindata",
    "porte_interne": "porta_interna",
    "porte_interne_ferrero_legno": "porta_interna",
    "portoncino": "porta_interna",
    "porta_da_cantiere": "porta_interna",
    "motori": "motori",
    "motori_22%": "motori",
    "accessori": "accessori_avvolgibile",
    "avvolgitore": "accessori_avvolgibile",
    "celini": "accessori_avvolgibile",
    "guide": "accessori_avvolgibile",
    "guide_fisse": "accessori_avvolgibile",
    "rulli": "accessori_avvolgibile",
    "cinghia": "accessori_avvolgibile",
    "thermoflex": "accessori_avvolgibile",
    "angolare": "accessori_avvolgibile",
    "coprifilo": "accessori_avvolgibile",
    "smoove": "accessori_avvolgibile",
    "situo_5_io_pure": "accessori_avvolgibile",
    "tahoma": "accessori_avvolgibile",
    "radiocomando_amy_1_io": "accessori_avvolgibile",
    "telecomandi": "accessori_avvolgibile",
    "apparecchio_a_sporgere": "accessori_avvolgibile",
    "ariete": "accessori_porta_blindata",
    "arietem": "accessori_porta_blindata",
    "cilindro": "accessori_porta_blindata",
    "spioncino_digitale": "accessori_porta_blindata",
    "controtelaio": "falegnameria",
    "listello": "falegnameria",
    "scuretto": "falegnameria",
    "profilo": "falegnameria",
    "lamiera": "falegnameria",
    "bancale": "falegnameria",
    "pannello": "falegnameria",
    "telaio": "falegnameria",
    "vetro": "falegnameria",
    "guarnizione": "falegnameria",
    "ferramenta": "falegnameria",
    "maniglia": "falegnameria",
    "fermavetro": "falegnameria",
    "piatto": "falegnameria",
}

POINTING_TAGLIA_MAP = [
    {"taglia": "xs", "valore": 1, "min": 0},
    {"taglia": "s", "valore": 3, "min": 2.0},
    {"taglia": "m", "valore": 5, "min": 4.0},
    {"taglia": "l", "valore": 8, "min": 6.5},
    {"taglia": "xl", "valore": 13, "min": 10.5},
    {"taglia": "xxl", "valore": 21, "min": 17.0},
]


def add_filters(
    filters: list,
    tecnico: str | None,
    cliente_nome: str | None,
    status: int | None = None,
    fornitore: str | None = None,
    azienda: str | None = None,
    commerciale: str | None = None,
):
    if tecnico:
        tecnico_clean = tecnico.strip().lower()

        if tecnico_clean == "nuovi-ordini":
            filters.append(
                or_(
                    Progetti.tecnico.is_(None),
                    func.trim(Progetti.tecnico) == "",
                )
            )
        elif tecnico_clean != "generali":
            filters.append(Progetti.tecnico.ilike(f"%{tecnico.strip()}%"))

    if cliente_nome and cliente_nome.strip():
        filters.append(Cliente.nome_cliente.ilike(f"%{cliente_nome.strip()}%"))

    if status is not None:
        filters.append(
            func.coalesce(Progetti.status_percent, 0) == status
        )

    if azienda and azienda.strip():
        filters.append(
            Progetti.azienda.ilike(f"%{azienda.strip()}%")
        )

    if commerciale and commerciale.strip():
        filters.append(
            Progetti.commerciale.ilike(f"%{commerciale.strip()}%")
        )

    if fornitore and fornitore.strip():
        filters.append(
            Progetti.fornitori_links.any(
                ProgettoFornitoreLink.fornitore.has(
                    Fornitore.nome_cliente.ilike(
                        f"%{fornitore.strip()}%"
                    )
                )
            )
        )


def map_to_taglia(grezzo: float) -> dict:
    result = POINTING_TAGLIA_MAP[0]

    for entry in POINTING_TAGLIA_MAP:
        if grezzo >= entry["min"]:
            result = entry

    return {
        "point_taglia": result["taglia"],
        "point_valore": result["valore"],
    }


def _get_product_name(product) -> str:
    if isinstance(product, dict):
        return str(product.get("nome") or "")
    return str(getattr(product, "nome", "") or "")


def _get_product_quantity(product) -> float:
    if isinstance(product, dict):
        return float(product.get("quantita") or 0)
    return float(getattr(product, "quantita", 0) or 0)


def _is_real_supplier(prodotti: list) -> bool:
    for product in prodotti or []:
        nome_key = _get_product_name(product).lower().strip()
        if nome_key and nome_key not in POINTING_SERVICE_PRODUCTS:
            return True
    return False


def calculate_project_point_db(progetto: Progetti) -> dict:
    links = progetto.fornitori_links or []

    real_links = [
        link for link in links if _is_real_supplier(link.prodotti_fornitore or [])
    ]

    fornitori_factor = max(0, len(real_links) - 1) * 2

    prodotti_factor = 0.0
    warnings = []

    for link in links:
        for product in link.prodotti_fornitore or []:
            nome = _get_product_name(product)
            nome_key = nome.lower().strip()

            if not nome_key:
                continue

            if nome_key in POINTING_SERVICE_PRODUCTS:
                continue

            spec_key = POINTING_FORM_VALUE_TO_SPEC.get(nome_key)

            if not spec_key:
                warnings.append(f'Tipo prodotto non riconosciuto: "{nome}"')
                continue

            peso = POINTING_SPEC_WEIGHTS.get(spec_key, 0)
            quantita = _get_product_quantity(product)

            prodotti_factor += quantita * peso

    citta = (
        progetto.centro_di_costo
        or (progetto.cliente.citta if progetto.cliente else "")
        or ""
    )

    genova_bonus = 1 if "genova" in citta.lower() else 0

    point_grezzo = round(
        fornitori_factor + prodotti_factor + genova_bonus,
        2,
    )

    taglia_data = map_to_taglia(point_grezzo)

    return {
        "point_grezzo": point_grezzo,
        "point_taglia": taglia_data["point_taglia"],
        "point_valore": taglia_data["point_valore"],
        "point_details": {
            "fornitori_factor": fornitori_factor,
            "prodotti_factor": round(prodotti_factor, 2),
            "genova_bonus": genova_bonus,
            "real_fornitori_count": len(real_links),
            "warnings": warnings,
        },
    }


def fetch_from_gesty(endpoint: str) -> dict:
    """
    Fetch data from Gesty API with Bearer token authentication.
    Raises HTTPException on error.
    """
    if not API_BASE or not API_KEY:
        raise HTTPException(status_code=500, detail="API_BASE/API_KEY not configured")

    headers = {"Authorization": f"Bearer {API_KEY}"}
    url = f"{API_BASE}/{endpoint.strip('/')}/"

    try:
        resp = httpx.get(url, headers=headers)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gesty fetch error: {e}")

    if resp.status_code != 200:
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        raise HTTPException(status_code=resp.status_code, detail={"upstream": body})

    payload = resp.json()
    if not payload.get("success"):
        raise HTTPException(status_code=502, detail="Gesty returned success=false")

    return payload['data'] if 'data' in payload else payload


def extract_prodotti_names(db: Session, gesty_payload: Any) -> Dict[str, Any]:
    """
    Collect unique product names from the Gesty payload and insert missing ones.

    Accepts either:
      - a list[dict] like the sample you posted, or
      - a dict with a 'data' key containing that list.

    Returns a summary dict.
    """
    # Normalize input to a list of items
    if isinstance(gesty_payload, dict):
        items = gesty_payload.get("data") or []
    elif isinstance(gesty_payload, list):
        items = gesty_payload
    else:
        items = []

    # Traverse and collect unique product names
    names: Set[str] = set()
    for item in items:
        progetto = (item or {}).get("Progetto") or {}
        fornitori = (progetto or {}).get("fornitori") or {}
        if isinstance(fornitori, dict):
            for _, forn in fornitori.items():
                for prod in (forn or {}).get("prodotti", []) or []:
                    name = (prod or {}).get("prodotto")
                    if isinstance(name, str):
                        clean = name.strip()
                        if clean:
                            names.add(clean)

    if not names:
        return {"inserted": 0, "skipped": 0, "total_unique_seen": 0, "message": "No product names found in payload."}

    # Fetch existing product names from DB
    # Depending on SQLModel/engine, this can return list[str] or list[tuple]; normalize to set[str]
    existing_rows = db.exec(select(Prodotto.nome_prodotto)).all()
    existing_set = {row if isinstance(row, str) else row[0] for row in existing_rows}

    to_create = [Prodotto(nome_prodotto=n) for n in names if n not in existing_set]
    skipped = len(names) - len(to_create)

    inserted = 0
    if to_create:
        db.add_all(to_create)
        try:
            db.commit()
            inserted = len(to_create)
        except Exception:
            # On bulk insert race/unique conflicts, fall back to safe per-row inserts
            db.rollback()
            inserted_safe = 0
            for prod in to_create:
                try:
                    db.add(prod)
                    db.commit()
                    db.refresh(prod)
                    inserted_safe += 1
                except Exception:
                    db.rollback()  # likely unique collision; ignore
            inserted = inserted_safe

    return {
        "inserted": inserted,
        "skipped": skipped,
        "total_unique_seen": len(names),
        "sample": sorted(list(names))[:10],
    }


def attach_file_links(payload: list[dict]) -> list[dict]:
    """
    Replace contratto_code and rm_code with proxy URLs if present.
    """
    for item in payload:
        progetto = item.get("Progetto") or {}

        contratto_code = progetto.get("contratto_code")
        if contratto_code and isinstance(contratto_code, str) and contratto_code.strip():
            progetto["contratto_code"] = f"{BASE_URL}/getFiles/contratto/{contratto_code}"

        rm_code = progetto.get("rm_code")
        if rm_code and isinstance(rm_code, str) and rm_code.strip():
            progetto["rm_code"] = f"{BASE_URL}/getFiles/rm/{rm_code}"

    return payload


def create_clienti_from_payload(db: Session, payload: list[dict]) -> dict:
    created_ids: list[int] = []
    skipped: list[str] = []
    curr_date = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    for item in payload or []:
        raw_cliente = (item or {}).get("Cliente") or {}
        if not raw_cliente:
            continue

        # Normalize and fill defaults
        try:
            cliente_id = int(raw_cliente["id"]) if "id" in raw_cliente and str(raw_cliente["id"]).strip().isdigit() else None
        except Exception:
            cliente_id = None

        nome_cliente = (raw_cliente.get("nome_cliente") or "").strip()
        citta = (raw_cliente.get("citta") or "").strip()
        indirizzo = (raw_cliente.get("indirizzo") or "").strip()
        numero_tel = (raw_cliente.get("numero_tel") or "").strip()
        centro_di_costo = (raw_cliente.get("email") or "").strip()
        contatti = {}
        note = ""
        data_creazione = curr_date

        # Build and insert
        data = {
            "id": cliente_id,
            "nome_cliente": nome_cliente,
            "citta": citta,
            "indirizzo": indirizzo,
            "numero_tel": numero_tel,
            "centro_di_costo": centro_di_costo,
            "contatti": contatti,
            "note": note,
            "data_creazione": data_creazione,
        }

        obj = Cliente(**{k: v for k, v in data.items() if v is not None})
        db.add(obj)
        try:
            db.commit()
            db.refresh(obj)
            created_ids.append(obj.id)
        except Exception as e:
            db.rollback()
            skipped.append(f"insert_error:{cliente_id or nome_cliente}:{e}")

    return {"created": created_ids, "skipped": skipped}


def build_progetti_payloads(payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    results: List[Dict[str, Any]] = []
    # now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    for item in payload or []:
        cli = (item or {}).get("Cliente") or {}
        prj = (item or {}).get("Progetto") or {}

        # --- cliente_id directly from payload ---
        try:
            cliente_id = int(cli.get("id")) if cli.get("id") else None
        except Exception:
            cliente_id = None
        if not cliente_id:
            continue

        # --- project fields ---
        tecnico = ""   # not available, keep empty
        progetto_id = (prj.get("id") or "").strip()
        stato = "ATTIVO"
        commerciale = (prj.get("commerciale") or "").strip()
        data_creazione = (prj.get("data_primo_pagamento") or "").strip()
        try:
            importo = float(prj.get("importo", 0) or 0)
        except Exception:
            importo = 0.0
        azienda = (prj.get("azienda") or "").strip()
        centro_di_costo = (prj.get("centro_di_costo") or "").strip()
        upload_id = (prj.get("contratto_code") or "").strip()
        upload_id_progetto_files = (prj.get("contratto_code") or "").strip()

        # --- proj importo_parz ---
        cdc = centro_di_costo.strip().lower()
        aliquota = 0.042 if cdc == "genova" else 0.025
        importo_parz = importo * aliquota

        # --- fornitori ---
        rilievi = []
        contratti = []
        fornitori_out = []
        fornitori_src = (prj.get("fornitori") or {})
        if isinstance(fornitori_src, dict):
            for _, fdata in fornitori_src.items():
                fid_raw = (fdata or {}).get("id")
                try:
                    fornitore_id = int(fid_raw) if fid_raw else 0
                except Exception:
                    fornitore_id = 0

                prodotti_out = []
                for p in (fdata or {}).get("prodotti", []) or []:
                    prodotti_out.append({
                        "nome": (p.get("prodotto") or "").strip(),
                        "quantita": int(p.get("quantita") or 0)
                    })

                fornitori_out.append({
                    "fornitore_id": fornitore_id,
                    "contratti": contratti[:],
                    "rilievi_misure": rilievi[:],
                    "prodotti_fornitore": prodotti_out,
                })

        results.append({
            "tecnico": tecnico,
            "stato": stato,
            "progetto_id": progetto_id,
            "data_creazione": data_creazione,
            "data_cambiamento_stato": data_creazione,
            "importo": importo,
            "importo_parz": importo_parz,
            "commerciale": commerciale,
            "cliente_id": cliente_id,
            "azienda": azienda,
            "centro_di_costo": centro_di_costo,
            "fornitori": fornitori_out,
            "upload_id": upload_id,
            "upload_id_progetto_files": upload_id_progetto_files,
        })

    return results


async def fetch_pdf_from_crm(tipo: str, code: str) -> bytes:
    url = f"{API_BASE}/{tipo}/{code}/"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, headers=headers)

    if r.status_code == 200:
        return r.content

    if r.status_code in (401, 403):
        raise HTTPException(status_code=401, detail="Token non valido")

    raise HTTPException(status_code=r.status_code, detail=r.text)
