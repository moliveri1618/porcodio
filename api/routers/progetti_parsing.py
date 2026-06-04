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
    fornitori_with_ids = add_fornitore_ids(fornitori_data["fornitori"], db)
    print(fornitori_with_ids)
    print('\n')


    result = {
        "Cliente": cliente_info["Cliente"],
        "Progetto": progetto_info["Progetto"],
        "Fornitori": fornitori_with_ids,
    }
    return result
