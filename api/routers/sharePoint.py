from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, Form
from typing import List
from urllib.parse import quote
import json
import sys
import os
import requests
from typing import List
import json
from urllib.parse import quote
from datetime import datetime

# Allow relative imports when running in GitHub Actions
if os.getenv("GITHUB_ACTIONS"):
    sys.path.append(os.path.dirname(__file__))

router = APIRouter()

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET_VALUE = os.getenv("CLIENT_SECRET_VALUE")
CLIENT_SECRET_ID = os.getenv("CLIENT_SECRET_ID")
SHAREPOINT_HOST = os.getenv("SHAREPOINT_HOST")
SHAREPOINT_SITE_PATH = os.getenv("SHAREPOINT_SITE_PATH")
GRAPH_URL = os.getenv("GRAPH_URL")


async def upload_file_to_sharepoint(
    file: UploadFile,
    folder_path: str,
    token: str,
    drive_id: str,
):

    content = await file.read()

    full_path = f"{folder_path}/{file.filename}"

    encoded_path = quote(
        full_path,
        safe="/",
    )

    url = f"{GRAPH_URL}/drives/{drive_id}" f"/root:/{encoded_path}:/content"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream",
    }

    response = requests.put(
        url,
        headers=headers,
        data=content,
    )

    if not response.ok:
        raise HTTPException(
            status_code=response.status_code,
            detail={
                "file": file.filename,
                "path": full_path,
                "microsoft_error": response.text,
            },
        )

    uploaded = response.json()

    return {
        "file_name": uploaded["name"],
        "file_id": uploaded["id"],
        "web_url": uploaded["webUrl"],
        "path": full_path,
    }


# ---------------------------------------------------------
# GET ACCESS TOKEN
# ---------------------------------------------------------


def get_access_token():
    url = f"https://login.microsoftonline.com/" f"{TENANT_ID}/oauth2/v2.0/token"

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET_VALUE,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }

    response = requests.post(url, data=data)

    if not response.ok:
        raise HTTPException(
            status_code=500, detail=f"Microsoft auth failed: {response.text}"
        )

    return response.json()["access_token"]


# ---------------------------------------------------------
# GET SHAREPOINT SITE ID
# ---------------------------------------------------------


def get_site_id(token: str):

    url = f"{GRAPH_URL}/sites/" f"{SHAREPOINT_HOST}:" f"{SHAREPOINT_SITE_PATH}"

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)

    if not response.ok:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()["id"]


# ---------------------------------------------------------
# GET DEFAULT DOCUMENT LIBRARY / DRIVE
# ---------------------------------------------------------


def get_drive_id(token: str, site_id: str):

    url = f"{GRAPH_URL}/sites/{site_id}/drive"

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)

    if not response.ok:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()["id"]


# ---------------------------------------------------------
# UPLOAD FILE
# ---------------------------------------------------------


@router.post("/sharepoint/upload")
async def upload_to_sharepoint(
    file: UploadFile = File(...), folder: str = "06-Progetti"
):

    token = get_access_token()
    site_id = get_site_id(token)
    drive_id = get_drive_id(token, site_id)

    # return {
    #     "status": "connected",
    #     "site_id": site_id,
    #     "drive_id": drive_id,
    # }

    content = await file.read()

    # Example:
    # 06-Progetti/test.pdf
    path = f"{folder}/{file.filename}"

    url = f"{GRAPH_URL}/drives/{drive_id}" f"/root:/{path}:/content"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream",
    }

    response = requests.put(url, headers=headers, data=content)

    if not response.ok:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    uploaded = response.json()

    return {
        "message": "File uploaded successfully",
        "file_name": uploaded["name"],
        "file_id": uploaded["id"],
        "web_url": uploaded["webUrl"],
        "site_id": site_id,
        "drive_id": drive_id,
    }


# ---------------------------------------------------------
# UPLOAD FILE 2
# ---------------------------------------------------------


@router.post("/upload-project")
async def upload_project_to_sharepoint(request: Request):

    form = await request.form()

    print("FORM KEYS:", list(form.keys()))

    for key in form.keys():
        print("KEY:", key)
        print("VALUES:", form.getlist(key))

    cliente_id = form.get("cliente_id")
    cliente_nome = form.get("cliente_nome")

    if not cliente_id or not cliente_nome:
        raise HTTPException(
            status_code=400,
            detail="cliente_id and cliente_nome are required",
        )

    token = get_access_token()
    site_id = get_site_id(token)
    drive_id = get_drive_id(token, site_id)

    # find right month
    now = datetime.now()
    year = now.strftime("%Y")
    month_map = {
        1: "01 - Jan",
        2: "02 - Feb",
        3: "03 - Mar",
        4: "04 - Apr",
        5: "05 - May",
        6: "06 - Jun",
        7: "07 - Jul",
        8: "08 - Aug",
        9: "09 - Sep",
        10: "10 - Oct",
        11: "11 - Nov",
        12: "12 - Dec",
    }
    month = month_map[now.month]
    project_folder = f"{cliente_id} - {cliente_nome}"
    base_project_path = f"06-Progetti/" f"{year}/" f"{month}/" f"{project_folder}"

    uploaded_files = []

    # =====================================================
    # CONTRATTO
    # =====================================================

    contratto_files = form.getlist("contratto")

    for file in contratto_files:

        if not getattr(file, "filename", None):
            continue

        folder_path = f"{base_project_path}/" f"Contratto"

        uploaded = await upload_file_to_sharepoint(
            file=file,
            folder_path=folder_path,
            token=token,
            drive_id=drive_id,
        )

        uploaded_files.append(uploaded)

    # =====================================================
    # FIND FORNITORI
    # =====================================================

    fornitore_ids = set()

    for key in form.keys():

        # Example:
        # fornitore_1_nome
        # fornitore_26_nome

        if key.startswith("fornitore_") and key.endswith("_nome"):
            parts = key.split("_")

            if len(parts) >= 3:
                fornitore_ids.add(parts[1])

    # =====================================================
    # FORNITORI
    # =====================================================

    for fornitore_id in fornitore_ids:

        fornitore_nome = form.get(f"fornitore_{fornitore_id}_nome")

        if not fornitore_nome:
            continue

        # -----------------------------------------
        # ORDINE
        # -----------------------------------------

        ordine_files = form.getlist(f"fornitore_{fornitore_id}_ordine")

        for file in ordine_files:

            if not getattr(file, "filename", None):
                continue

            folder_path = (
                f"{base_project_path}/"
                f"Fornitori/"
                f"{fornitore_nome}/"
                f"Ordine"
            )

            uploaded = await upload_file_to_sharepoint(
                file=file,
                folder_path=folder_path,
                token=token,
                drive_id=drive_id,
            )

            uploaded_files.append(uploaded)

        # -----------------------------------------
        # CONFERMA ORDINE
        # -----------------------------------------

        conferma_files = form.getlist(f"fornitore_{fornitore_id}_conferma_ordine")

        for file in conferma_files:

            if not getattr(file, "filename", None):
                continue

            folder_path = (
                f"{base_project_path}/"
                f"Fornitori/"
                f"{fornitore_nome}/"
                f"Conferma Ordine"
            )

            uploaded = await upload_file_to_sharepoint(
                file=file,
                folder_path=folder_path,
                token=token,
                drive_id=drive_id,
            )

            uploaded_files.append(uploaded)

    return {
        "message": "Files uploaded successfully",
        "cliente_id": cliente_id,
        "cliente_nome": cliente_nome,
        "uploaded_count": len(uploaded_files),
        "files": uploaded_files,
    }
