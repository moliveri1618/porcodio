from fastapi import APIRouter, UploadFile, File
import os
import sys

if os.getenv("GITHUB_ACTIONS"):
    sys.path.append(os.path.dirname(__file__))
from routers.utils_parsing import *

router = APIRouter()

@router.post("/parse_contratto_pdf/")
async def pdf_parse_contratto(file: UploadFile = File(...)):

    # Get text form pdf 
    text_content = pdf_to_text_from_upload(file)

    ## Extract cliente info
    cliente_info = extract_cliente_info(text_content)
    print(cliente_info)
    print('\n')

    ## Extract progetto info
    progetto_info = extract_progetto_info(text_content)
    # print(progetto_info)
    # print('\n')

    ## Extract Fornitori Data
    fornitori_data = pdf_rules2(text_content)
    fornitori_data = build_fornitori_dict(fornitori_data)
    # print(fornitori_data)
    # print('\n')

    # Merge fornitori into progetto
    progetto_info["Progetto"]["fornitori"] = fornitori_data["fornitori"]
    print(progetto_info)
    print('\n')

    ## Build result
    result = {
        "Cliente": cliente_info["Cliente"],
        "Progetto": progetto_info["Progetto"],
    }
    return result
