from collections import defaultdict

from fastapi import APIRouter, Depends, UploadFile, File
import os
import sys

if os.getenv("GITHUB_ACTIONS"):
    sys.path.append(os.path.dirname(__file__))
from dependecies import get_db
from routers.utils_parsing import *

router = APIRouter()

def parse_contratto_text_v2(
    text_content: str,
    db: Session,
):
    
    ## Extract cliente info
    cliente_info = extract_cliente_info(text_content, db)
    # print(cliente_info)
    # print("\n")

    ## Extract progetto info
    progetto_info = extract_progetto_info(text_content)
    # print(progetto_info)
    # print("\n")

    ## Extract Fornitori Data
    fornitori_data = pdf_rules2(text_content)
    fornitori_data_w_ids = add_fornitore_ids(fornitori_data["fornitori"], db)
    # print(fornitori_data_w_ids)
    # print("\n")
    #print("fornitori_data_w_ids:", fornitori_data_w_ids)

    ## Build schede tecniche fornitore
    schede_tecniche = {}

    for fornitore in fornitori_data_w_ids:
        fornitore_id = fornitore.get("fornitore_id")
        design = fornitore.get("Design") or ""
        quantita = int(fornitore.get("Quantita") or 1)

        if not fornitore_id:
            continue

        tipo_prodotto_id = (
            1 if normalize_design(design) == normalize_design("Avvolgibile") else 3
        )

        scheda = build_scheda_tecnica_schema_fornitore(
            fornitore_id=fornitore_id,
            quantita=quantita,
            tipo_prodotto_id=tipo_prodotto_id,
            db=db,
        )

        if tipo_prodotto_id == 3:
            for gruppo in scheda:
                gruppo["tipo_prodotto_nome"] = design

        schede_tecniche.setdefault(fornitore_id, []).extend(scheda)

    ## Match selected values from PDF with schede tecniche
    schede_tecnich_sel_value = enrich_schede_with_selected_values_V2(
        fornitori_data_w_ids,
        schede_tecniche,
    )

    schede_tecniche_result = {}

    for fornitore in fornitori_data_w_ids:
        fornitore_id = fornitore.get("fornitore_id")
        fornitore_nome = fornitore.get("Fornitore")

        if not fornitore_id:
            continue

        scheda = (
            schede_tecnich_sel_value.get(fornitore_id)
            or schede_tecnich_sel_value.get(str(fornitore_id))
        )

        schede_tecniche_result[fornitore_id] = {
            "fornitore_id": fornitore_id,
            "fornitore": fornitore_nome,
            "value": scheda if scheda else None,
        }

    result = {
        "Cliente": cliente_info["Cliente"],
        "Progetto": progetto_info["Progetto"],
        "Fornitori": fornitori_data_w_ids,
        "SchedeTecniche": schede_tecniche_result,
    }

    return result

@router.post("/parse_contratto_pdf/V3")
async def pdf_parse_contratto(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    text_content = pdf_to_text_from_upload(file)

    result = parse_contratto_text_v2(
        text_content,
        db,
    )

    return result


@router.post("/parse_contratto_pdf/V2")
async def pdf_parse_contratto(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    # Get text from pdf
    text_content = pdf_to_text_from_upload(file)
    # print(text_content)
    # print('\n')

    ## Extract cliente info
    cliente_info = extract_cliente_info(text_content, db)
    # print(cliente_info)
    # print("\n")

    ## Extract progetto info
    progetto_info = extract_progetto_info(text_content)
    # print(progetto_info)
    # print("\n")

    ## Extract Fornitori Data
    fornitori_data = pdf_rules2(text_content)
    fornitori_data_w_ids = add_fornitore_ids(fornitori_data["fornitori"], db)
    # print(fornitori_data_w_ids)
    # print("\n")
    #print("fornitori_data_w_ids:", fornitori_data_w_ids)

    ## Build schede tecniche fornitore
    schede_tecniche = {}

    for fornitore in fornitori_data_w_ids:
        fornitore_id = fornitore.get("fornitore_id")
        design = fornitore.get("Design") or ""
        quantita = int(fornitore.get("Quantita") or 1)

        if not fornitore_id:
            continue

        tipo_prodotto_id = (
            1 if normalize_design(design) == normalize_design("Avvolgibile") else 3
        )

        scheda = build_scheda_tecnica_schema_fornitore(
            fornitore_id=fornitore_id,
            quantita=quantita,
            tipo_prodotto_id=tipo_prodotto_id,
            db=db,
        )

        if tipo_prodotto_id == 3:
            for gruppo in scheda:
                gruppo["tipo_prodotto_nome"] = design

        schede_tecniche.setdefault(fornitore_id, []).extend(scheda)

    ## Match selected values from PDF with schede tecniche
    schede_tecnich_sel_value = enrich_schede_with_selected_values_V2(
        fornitori_data_w_ids,
        schede_tecniche,
    )

    schede_tecniche_result = {}

    for fornitore in fornitori_data_w_ids:
        fornitore_id = fornitore.get("fornitore_id")
        fornitore_nome = fornitore.get("Fornitore")

        if not fornitore_id:
            continue

        scheda = (
            schede_tecnich_sel_value.get(fornitore_id)
            or schede_tecnich_sel_value.get(str(fornitore_id))
        )

        schede_tecniche_result[fornitore_id] = {
            "fornitore_id": fornitore_id,
            "fornitore": fornitore_nome,
            "value": scheda if scheda else None,
        }

    result = {
        "Cliente": cliente_info["Cliente"],
        "Progetto": progetto_info["Progetto"],
        "Fornitori": fornitori_data_w_ids,
        "SchedeTecniche": schede_tecniche_result,
    }
    return result
