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
    schede_tecniche = {}
    for fornitore in fornitori_data_w_ids:
        fornitore_id = fornitore.get("fornitore_id")
        if fornitore_id and fornitore_id not in schede_tecniche:
            schede_tecniche[fornitore_id] = build_scheda_tecnica_schema_fornitore(
                fornitore_id=fornitore_id,
                db=db,
            )

    result = {
        "Cliente": cliente_info["Cliente"],
        "Progetto": progetto_info["Progetto"],
        "Fornitori": fornitori_data_w_ids,
        "SchedeTecniche": schede_tecniche,
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
