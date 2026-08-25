# routers/scheda_tecnica_pezzo.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlmodel import Session, select
from sqlalchemy import delete

from models.scheda_tecnica_pezzo import SchedaTecnicaPezzo
from models.scheda_tecnica_schema import SchedaTecnicaSchema
from schemas.scheda_tecnica_pezzo import (
    SchedaTecnicaPezzoRead,
)
from models.progetti import Progetti
from routers.utils_parsing import *

from dependecies import get_db

router = APIRouter()


# Upsert One
@router.post("/bulk/from-schede/{progetto_id}")
def save_schede_tecniche_from_frontend(
    progetto_id: int,
    schede_tecniche: dict,
    db: Session = Depends(get_db),
):

    # delete old values first
    db.exec(
        delete(SchedaTecnicaPezzo).where(SchedaTecnicaPezzo.progetto_id == progetto_id)
    )

    new_rows = []

    for scheda_wrapper in schede_tecniche.values():
        schede = scheda_wrapper.get("value")

        if not schede:
            continue

        for scheda_index, scheda in enumerate(schede):
            tipo_prodotto_nome = scheda.get("tipo_prodotto_nome")

            for rif in scheda.get("riferimenti", []):
                riferimento = rif.get("riferimento")
                posizione = rif.get("posizione")
                values = rif.get("values", {})

                for schema_id, valore in values.items():
                    db_pezzo = SchedaTecnicaPezzo(
                        progetto_id=progetto_id,
                        riferimento=riferimento,
                        posizione=posizione,
                        scheda_tecnica_schema_id=int(schema_id),
                        valore=str(valore) if valore is not None else None,
                        tipo_prodotto_nome=tipo_prodotto_nome,
                        scheda_index=scheda_index,
                    )

                    db.add(db_pezzo)
                    new_rows.append(db_pezzo)

    db.commit()

    return {"created": len(new_rows)}


# Get one
@router.get("/by-progetto/{progetto_id}")
def get_schede_tecniche_by_progetto(
    progetto_id: int,
    db: Session = Depends(get_db),
):
    progetto = db.get(Progetti, progetto_id)

    if not progetto:
        raise HTTPException(status_code=404, detail="Progetto not found")

    final_result = {}

    # 1. Add all fornitori of the progetto first, with value null
    for link in progetto.fornitori_links:
        if not link.fornitore:
            continue

        fid = str(link.fornitore_id)

        final_result[fid] = {
            "fornitore_id": link.fornitore_id,
            "fornitore": link.fornitore.nome_cliente,
            "value": None,
        }

    # 2. Get saved schede tecniche pezzi
    pezzi = db.exec(
        select(SchedaTecnicaPezzo).where(SchedaTecnicaPezzo.progetto_id == progetto_id)
    ).all()

    result = {}

    for pezzo in pezzi:
        schema = db.get(SchedaTecnicaSchema, pezzo.scheda_tecnica_schema_id)

        if not schema:
            continue

        fornitore_id = str(schema.fornitore_id)

        if fornitore_id not in result:
            result[fornitore_id] = {}

        tipo_prodotto_nome = pezzo.tipo_prodotto_nome or "Altro"
        tipo_key = f"{schema.tipo_prodotto_id}:{tipo_prodotto_nome}"

        if tipo_key not in result[fornitore_id]:
            result[fornitore_id][tipo_key] = {
                "tipo_prodotto_id": schema.tipo_prodotto_id,
                "tipo_prodotto_nome": tipo_prodotto_nome,
                "quantita": 0,
                "campi": [],
                "riferimenti": {},
            }

        group = result[fornitore_id][tipo_key]

        if pezzo.riferimento not in group["riferimenti"]:
            group["riferimenti"][pezzo.riferimento] = {
                "riferimento": pezzo.riferimento,
                "posizione": pezzo.posizione,
                "values": {},
            }
        elif (
            group["riferimenti"][pezzo.riferimento]["posizione"] is None
            and pezzo.posizione is not None
        ):
            group["riferimenti"][pezzo.riferimento]["posizione"] = pezzo.posizione

        group["riferimenti"][pezzo.riferimento]["values"][
            str(pezzo.scheda_tecnica_schema_id)
        ] = pezzo.valore

    # 3. Add schede into the fornitori wrapper
    for fornitore_id, tipi in result.items():
        if fornitore_id not in final_result:
            final_result[fornitore_id] = {
                "fornitore_id": int(fornitore_id),
                "fornitore": None,
                "value": [],
            }

        final_result[fornitore_id]["value"] = []

        for group in tipi.values():
            riferimenti = list(group["riferimenti"].values())
            quantita = len(riferimenti)

            schede_base = build_scheda_tecnica_schema_fornitore(
                fornitore_id=int(fornitore_id),
                quantita=quantita,
                tipo_prodotto_id=group["tipo_prodotto_id"],
                db=db,
            )

            if not schede_base:
                continue

            scheda = schede_base[0]
            scheda["tipo_prodotto_nome"] = group["tipo_prodotto_nome"]
            scheda["riferimenti"] = riferimenti
            scheda["quantita"] = quantita

            final_result[fornitore_id]["value"].append(scheda)

    return final_result


# Get all
@router.get("", response_model=List[SchedaTecnicaPezzoRead])
def read_schede_tecniche_pezzi(db: Session = Depends(get_db)):
    schede = db.exec(select(SchedaTecnicaPezzo)).all()
    return schede
