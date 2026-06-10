from collections import defaultdict

from fastapi import APIRouter, Depends, UploadFile, File
import os
import sys

if os.getenv("GITHUB_ACTIONS"):
    sys.path.append(os.path.dirname(__file__))
from dependecies import get_db
from routers.utils_parsing import *

router = APIRouter()


@router.post("/parse_contratto_pdf")
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
    print(cliente_info)
    print('\n')

    ## Extract progetto info
    progetto_info = extract_progetto_info(text_content)
    print(progetto_info)
    print('\n')

    ## Extract Fornitori Data
    fornitori_data = pdf_rules2(text_content)
    fornitori_data_w_ids = add_fornitore_ids(fornitori_data["fornitori"], db)
    print(fornitori_data_w_ids)
    print('\n')

    ## Build schede tecniche fornitore
    schede_quantita = defaultdict(int)
    for fornitore in fornitori_data_w_ids:
        if normalize_design(fornitore.get("Design")) != normalize_design("Avvolgibile"):   # build table just for avvolgibili
            continue 
        fornitore_id = fornitore.get("fornitore_id")
        if not fornitore_id:
            continue
        schede_quantita[fornitore_id] += int(fornitore.get("Quantita") or 1)

    schede_tecniche = {
        fornitore_id: build_scheda_tecnica_schema_fornitore(
            fornitore_id=fornitore_id,
            quantita=quantita,
            db=db,
        )
        for fornitore_id, quantita in schede_quantita.items()
    }

    ## Match selected values from PDF with schede tecniche
    schede_tecnich_sel_value = enrich_schede_with_selected_values(
        fornitori_data_w_ids,
        schede_tecniche,
    )

    result = {
        "Cliente": cliente_info["Cliente"],
        "Progetto": progetto_info["Progetto"],
        "Fornitori": fornitori_data_w_ids,
        "SchedeTecniche": schede_tecnich_sel_value,
    }
    return result


@router.get("/{progetto_id}/{fornitore_id}")
def schede_tecniche_fornitore_get(
    progetto_id: int,
    fornitore_id: int,
    db: Session = Depends(get_db),
):
    return get_schede_tecniche_fornitore(
        progetto_id=progetto_id,
        fornitore_id=fornitore_id,
        db=db,
    )
