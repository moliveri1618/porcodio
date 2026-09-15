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


def find_project_folder_by_id(
    progetto_id: str,
    token: str,
    drive_id: str,
    data_creazione: str,
):

    print("\n========== SHAREPOINT PROJECT SEARCH ==========")
    print("1. progetto_id:", repr(progetto_id))
    print("2. data_creazione:", repr(data_creazione))

    year, month_num, _ = data_creazione.split("-")

    month_map = {
        "01": "01 - Jan",
        "02": "02 - Feb",
        "03": "03 - Mar",
        "04": "04 - Apr",
        "05": "05 - May",
        "06": "06 - Jun",
        "07": "07 - Jul",
        "08": "08 - Aug",
        "09": "09 - Sep",
        "10": "10 - Oct",
        "11": "11 - Nov",
        "12": "12 - Dec",
    }

    month = month_map[month_num]

    print("3. year:", year)
    print("4. month:", month)

    search_folder = f"06-Progetti/{year}/{month}"
    encoded_folder = quote(search_folder, safe="/")

    print("5. search_folder:", search_folder)
    print("6. encoded_folder:", encoded_folder)

    url = (
        f"{GRAPH_URL}/drives/{drive_id}/root:"
        f"/{encoded_folder}:/children"
    )

    print("7. SEARCH URL:", url)

    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = requests.get(url, headers=headers)

    print("8. HTTP STATUS:", response.status_code)
    print("9. RAW RESPONSE:", response.text)

    if not response.ok:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Could not search SharePoint: {response.text}",
        )

    items = response.json().get("value", [])

    print("10. NUMBER OF RESULTS:", len(items))

    expected_prefix = f"{progetto_id}_"

    print("11. EXPECTED PREFIX:", repr(expected_prefix))

    # for item in items:

    #     # We only care about folders
    #     if "folder" not in item:
    #         continue

    #     folder_name = item.get("name", "")

    #     # Example:
    #     # 29855 - Mario Rossi_348
    #     if folder_name.startswith(expected_prefix):
    #         return item

    # return None
    for index, item in enumerate(items):

        folder_name = item.get("name", "")
        is_folder = "folder" in item

        print(f"\n--- RESULT {index} ---")
        print("NAME:", repr(folder_name))
        print("IS FOLDER:", is_folder)
        print("ID:", item.get("id"))
        print("STARTS WITH EXPECTED PREFIX:", folder_name.startswith(expected_prefix))

        parent = item.get("parentReference", {})
        print("PARENT PATH:", parent.get("path"))

        if not is_folder:
            print("SKIP -> result is not a folder")
            continue

        if folder_name.startswith(expected_prefix):
            print(">>> MATCH FOUND:", folder_name)
            print(">>> PROJECT WILL BE SKIPPED")
            print("===============================================\n")
            return item

        print("NO MATCH ->", repr(folder_name), "does not start with", repr(expected_prefix))

    print("\n>>> NO EXISTING PROJECT FOUND")
    print(">>> UPLOAD WILL CONTINUE")
    print("===============================================\n")

    return None

# =====================================================
# CHECK IF PROJECT ALREADY EXISTS
# =====================================================


@router.get("/project-exists")
def project_exists(
    progetto_id: int,
    data_creazione: str,
):
    token = get_access_token()
    site_id = get_site_id(token)
    drive_id = get_drive_id(token, site_id)

    existing_project = find_project_folder_by_id(
        progetto_id=progetto_id,
        token=token,
        data_creazione=data_creazione,
        drive_id=drive_id,
    )

    # Project already exists
    if existing_project:
        return {
            "exists": True,
            "progetto_id": progetto_id,
            "folder_name": existing_project.get("name"),
            "folder_id": existing_project.get("id"),
            "web_url": existing_project.get("webUrl"),
        }

    # Project does not exist
    return {
        "exists": False,
        "progetto_id": progetto_id,
        "folder_name": None,
        "folder_id": None,
        "web_url": None,
    }


# ---------------------------------------------------------
# UPLOAD FILE 2
# ---------------------------------------------------------


@router.post("/upload-project")
async def upload_project_to_sharepoint(request: Request):

    form = await request.form()

    # print("FORM KEYS:", list(form.keys()))

    # for key in form.keys():
    #     print("KEY:", key)
    # print("VALUES:", form.getlist(key))

    cliente_id = form.get("cliente_id")
    cliente_nome = form.get("cliente_nome")
    progetto_id = form.get("progetto_id")
    data_creazione = form.get("data_creazione")

    if not progetto_id or not cliente_id or not cliente_nome or not data_creazione:
        raise HTTPException(
            status_code=400,
            detail="progetto_id, cliente_id, cliente_nome and data_creazione are required",
        )

    token = get_access_token()
    site_id = get_site_id(token)
    drive_id = get_drive_id(token, site_id)

    # =====================================================
    # CHECK IF PROJECT ALREADY EXISTS
    # =====================================================

    existing_project = find_project_folder_by_id(
        progetto_id=progetto_id,
        token=token,
        data_creazione=data_creazione,
        drive_id=drive_id,
    )

    if existing_project:
        return {
            "message": "Project already exists in SharePoint. Upload skipped.",
            "skipped": True,
            "progetto_id": progetto_id,
            "folder_name": existing_project.get("name"),
            "folder_id": existing_project.get("id"),
            "web_url": existing_project.get("webUrl"),
        }

    # find right month
    year, month_num, _ = data_creazione.split("-")
    month_map = {
        "01": "01 - Jan",
        "02": "02 - Feb",
        "03": "03 - Mar",
        "04": "04 - Apr",
        "05": "05 - May",
        "06": "06 - Jun",
        "07": "07 - Jul",
        "08": "08 - Aug",
        "09": "09 - Sep",
        "10": "10 - Oct",
        "11": "11 - Nov",
        "12": "12 - Dec",
    }
    month = month_map[month_num]
    project_folder = f"{progetto_id}_{cliente_nome}"
    base_project_path = f"06-Progetti/" f"{year}/" f"{month}/" f"{project_folder}"

    uploaded_files = []

    # =====================================================
    # CONTRATTO
    # =====================================================

    contratto_files = form.getlist("contratto")

    for file in contratto_files:

        if not getattr(file, "filename", None):
            continue

        folder_path = base_project_path

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

            folder_path = f"{base_project_path}/" f"{fornitore_nome}"

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

            folder_path = f"{base_project_path}/" f"{fornitore_nome}"

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
