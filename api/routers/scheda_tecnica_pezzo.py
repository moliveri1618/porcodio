# routers/scheda_tecnica_pezzo.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlmodel import Session, select

from models.scheda_tecnica_pezzo import SchedaTecnicaPezzo
from models.scheda_tecnica_schema import SchedaTecnicaSchema
from schemas.scheda_tecnica_pezzo import (
    SchedaTecnicaPezzoCreate,
    SchedaTecnicaPezzoRead,
    SchedaTecnicaPezzoUpdate,
)
from models.progetti import Progetti
from models.progetto_fornitore_link import ProgettoFornitoreLink
from routers.utils_parsing import *

from dependecies import get_db

router = APIRouter()


# Create
@router.post("", response_model=SchedaTecnicaPezzoRead, status_code=201)
def create_scheda_tecnica_pezzo(
    scheda: SchedaTecnicaPezzoCreate,
    db: Session = Depends(get_db),
):
    db_scheda = SchedaTecnicaPezzo(**scheda.dict())
    db.add(db_scheda)
    db.commit()
    db.refresh(db_scheda)
    return db_scheda


@router.post("/bulk/from-schede/{progetto_id}")
def save_schede_tecniche_from_frontend(
    progetto_id: int,
    schede_tecniche: dict,
    db: Session = Depends(get_db),
):
    new_rows = []

    for scheda_wrapper in schede_tecniche.values():
        schede = scheda_wrapper.get("value")

        if not schede:
            continue

        for scheda in schede:
            for rif in scheda.get("riferimenti", []):
                riferimento = rif.get("riferimento")
                values = rif.get("values", {})

                for schema_id, valore in values.items():
                    db_pezzo = SchedaTecnicaPezzo(
                        progetto_id=progetto_id,
                        riferimento=riferimento,
                        scheda_tecnica_schema_id=int(schema_id),
                        valore=str(valore) if valore is not None else None,
                    )

                    db.add(db_pezzo)
                    new_rows.append(db_pezzo)

    db.commit()

    return {"created": len(new_rows)}


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

        tipo_key = str(schema.tipo_prodotto_id)

        if tipo_key not in result[fornitore_id]:
            result[fornitore_id][tipo_key] = {
                "tipo_prodotto_id": schema.tipo_prodotto_id,
                "tipo_prodotto_nome": None,
                "quantita": 0,
                "campi": [],
                "riferimenti": {},
            }

        group = result[fornitore_id][tipo_key]

        if pezzo.riferimento not in group["riferimenti"]:
            group["riferimenti"][pezzo.riferimento] = {
                "riferimento": pezzo.riferimento,
                "values": {},
            }

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
                db=db,
            )

            if not schede_base:
                continue

            scheda = schede_base[0]
            scheda["riferimenti"] = riferimenti
            scheda["quantita"] = quantita

            final_result[fornitore_id]["value"].append(scheda)

    return final_result


# @router.post("/bulk", response_model=List[SchedaTecnicaPezzoRead], status_code=201)
# def create_schede_tecniche_pezzi_bulk(
#     pezzi: List[SchedaTecnicaPezzoCreate],
#     db: Session = Depends(get_db),
# ):
#     db_pezzi = [SchedaTecnicaPezzo(**pezzo.model_dump()) for pezzo in pezzi]

#     db.add_all(db_pezzi)
#     db.commit()

#     for pezzo in db_pezzi:
#         db.refresh(pezzo)

#     return db_pezzi


# Get all
@router.get("", response_model=List[SchedaTecnicaPezzoRead])
def read_schede_tecniche_pezzi(db: Session = Depends(get_db)):
    schede = db.exec(select(SchedaTecnicaPezzo)).all()
    return schede


# Get one
@router.get("/{scheda_id}", response_model=SchedaTecnicaPezzoRead)
def read_scheda_tecnica_pezzo(
    scheda_id: int,
    db: Session = Depends(get_db),
):
    scheda = db.get(SchedaTecnicaPezzo, scheda_id)

    if not scheda:
        raise HTTPException(status_code=404, detail="Scheda tecnica pezzo not found")

    return scheda


# Put
@router.put("/{scheda_id}", response_model=SchedaTecnicaPezzoRead)
def update_scheda_tecnica_pezzo(
    scheda_id: int,
    scheda_update: SchedaTecnicaPezzoUpdate,
    db: Session = Depends(get_db),
):
    scheda = db.get(SchedaTecnicaPezzo, scheda_id)

    if not scheda:
        raise HTTPException(status_code=404, detail="Scheda tecnica pezzo not found")

    update_data = scheda_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(scheda, key, value)

    db.add(scheda)
    db.commit()
    db.refresh(scheda)

    return scheda


# Delete
@router.delete("/{scheda_id}", status_code=204)
def delete_scheda_tecnica_pezzo(
    scheda_id: int,
    db: Session = Depends(get_db),
):
    scheda = db.get(SchedaTecnicaPezzo, scheda_id)

    if not scheda:
        raise HTTPException(status_code=404, detail="Scheda tecnica pezzo not found")

    db.delete(scheda)
    db.commit()
