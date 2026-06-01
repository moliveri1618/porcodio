from fastapi import APIRouter, UploadFile, File
import os
import sys

if os.getenv("GITHUB_ACTIONS"):
    sys.path.append(os.path.dirname(__file__))
from routers.utils_parsing import *

router = APIRouter()


@router.post("/pdf_compare_contratto_ordine/")
async def pdf_compare_contratto_ordine(file: UploadFile = File(...)):
    pdf_path = save_pdf(file, "Files_contratto_ordine")

    return {
        "message": "PDF saved successfully",
        "pdf_path": pdf_path,
    }
