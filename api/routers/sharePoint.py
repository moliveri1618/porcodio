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
from io import BytesIO

# Allow relative imports when running in GitHub Actions
if os.getenv("GITHUB_ACTIONS"):
    sys.path.append(os.path.dirname(__file__))

from routers.utils import fetch_pdf_from_crm

router = APIRouter()

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET_VALUE = os.getenv("CLIENT_SECRET_VALUE")
CLIENT_SECRET_ID = os.getenv("CLIENT_SECRET_ID")
SHAREPOINT_HOST = os.getenv("SHAREPOINT_HOST")
SHAREPOINT_SITE_PATH = os.getenv("SHAREPOINT_SITE_PATH")
GRAPH_URL = os.getenv("GRAPH_URL")

# Fornitore id 2 is the fixed "Dati Cantiere" entry (see routers/progetti.py)
DATI_CANTIERE_FORNITORE_ID = "2"
DATI_CANTIERE_FOLDER_NAME = "Dati Cantiere"

# Gesty projects have upload_id = {BASE_URL}/getFiles/contratto/{code} (see attach_file_links)
GESTY_CONTRATTO_URL_MARKER = "/getFiles/contratto/"


async def upload_file_to_sharepoint(
    file: UploadFile,
    folder_path: str,
    token: str,
    drive_id: str,
    file_name: str | None = None,
):

    # Rewind so the same UploadFile can be uploaded to more than one folder
    await file.seek(0)
    content = await file.read()

    file_name = file_name or file.filename
    full_path = f"{folder_path}/{file_name}"

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
                "file": file_name,
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


async def upload_dati_cantiere_copy(
    file: UploadFile,
    year: str,
    project_folder: str,
    token: str,
    drive_id: str,
):
    """
    Upload a copy of a Dati Cantiere file to the year-level
    06-Progetti/{year}/Dati Cantiere folder.
    The file name is prefixed with the project folder name
    ({progetto_id}_{cliente_nome}) so files from different projects
    don't overwrite each other; re-uploading the same file replaces it.
    """

    prefix = f"{project_folder}_"
    file_name = file.filename or ""
    if not file_name.startswith(prefix):
        file_name = f"{prefix}{file_name}"

    return await upload_file_to_sharepoint(
        file=file,
        folder_path=f"06-Progetti/{year}/{DATI_CANTIERE_FOLDER_NAME}",
        token=token,
        drive_id=drive_id,
        file_name=file_name,
    )


def get_gesty_contratto_code(upload_id: str | None) -> str | None:
    """Contratto code if upload_id is a Gesty URL (.../getFiles/contratto/<code>), else None (S3 key / UUID)."""
    if not upload_id or GESTY_CONTRATTO_URL_MARKER not in upload_id:
        return None
    code = upload_id.rstrip("/").split("/")[-1].strip()
    return code or None


def folder_has_file(folder_id: str, file_name: str, token: str, drive_id: str) -> bool:
    """True if the SharePoint folder directly contains a file with this name (case-insensitive)."""
    url = f"{GRAPH_URL}/drives/{drive_id}/items/{folder_id}/children?$select=name,file&$top=999"
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})

    if not response.ok:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Could not list SharePoint folder: {response.text}",
        )

    target = file_name.lower()
    return any(
        "file" in item and item.get("name", "").lower() == target
        for item in response.json().get("value", [])
    )


async def ensure_gesty_contratto_on_sharepoint(
    upload_id: str | None,
    existing_project: dict | None,
    folder_path: str,
    token: str,
    drive_id: str,
) -> dict | None:
    """
    Gesty contracts are not on S3: download the PDF from Tigullio and upload it
    to the project folder, unless the folder already contains it.
    Returns None for non-Gesty projects. Errors are reported, not raised,
    so the rest of the SharePoint upload is not blocked.
    """
    code = get_gesty_contratto_code(upload_id)
    if not code:
        return None

    file_name = f"contratto-{code}.pdf"  # same name used by /getFiles/contratto/{code}

    try:
        if existing_project and folder_has_file(
            existing_project["id"], file_name, token, drive_id
        ):
            return {
                "status": "already_present",
                "file_name": file_name,
                "path": f"{folder_path}/{file_name}",
            }

        pdf_bytes = await fetch_pdf_from_crm("contratto", code)

        uploaded = await upload_file_to_sharepoint(
            file=UploadFile(file=BytesIO(pdf_bytes), filename=file_name),
            folder_path=folder_path,
            token=token,
            drive_id=drive_id,
        )
        return {"status": "uploaded", **uploaded}

    except HTTPException as e:
        print("GESTY CONTRATTO SHAREPOINT ERROR:", file_name, e.detail)
        return {"status": "error", "file_name": file_name, "detail": e.detail}



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

    # Check if rilievo misure is added, then dont skip upload
    allow_existing_project = (
        str(form.get("allow_existing_project", "false")).lower() == "true"
    )

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

    # =====================================================
    # GESTY CONTRATTO (not on S3): upload it if the folder doesn't have it yet
    # =====================================================

    gesty_contratto = await ensure_gesty_contratto_on_sharepoint(
        upload_id=form.get("upload_id"),
        existing_project=existing_project,
        folder_path=(
            f"06-Progetti/{year}/{month}/{existing_project.get('name')}"
            if existing_project
            else base_project_path
        ),
        token=token,
        drive_id=drive_id,
    )

    if existing_project and not allow_existing_project:
        return {
            "message": "Project already exists in SharePoint. Upload skipped.",
            "skipped": True,
            "progetto_id": progetto_id,
            "folder_name": existing_project.get("name"),
            "folder_id": existing_project.get("id"),
            "web_url": existing_project.get("webUrl"),
            "gesty_contratto": gesty_contratto,
        }

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
    # RILIEVO MISURE
    # =====================================================

    rilievo_files = form.getlist("rilievo_misure")

    for file in rilievo_files:
        if not getattr(file, "filename", None):
            continue

        uploaded = await upload_file_to_sharepoint(
            file=file,
            folder_path=f"{base_project_path}/RilievoMisure",
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

        is_dati_cantiere = fornitore_id == DATI_CANTIERE_FORNITORE_ID

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

            # Dati Cantiere: also keep a copy in 06-Progetti/{year}/Dati Cantiere
            if is_dati_cantiere:
                uploaded_files.append(
                    await upload_dati_cantiere_copy(
                        file=file,
                        year=year,
                        project_folder=project_folder,
                        token=token,
                        drive_id=drive_id,
                    )
                )

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

            # Dati Cantiere: also keep a copy in 06-Progetti/{year}/Dati Cantiere
            if is_dati_cantiere:
                uploaded_files.append(
                    await upload_dati_cantiere_copy(
                        file=file,
                        year=year,
                        project_folder=project_folder,
                        token=token,
                        drive_id=drive_id,
                    )
                )

    return {
        "message": "Files uploaded successfully",
        "cliente_id": cliente_id,
        "cliente_nome": cliente_nome,
        "uploaded_count": len(uploaded_files),
        "files": uploaded_files,
        "gesty_contratto": gesty_contratto,
    }


# ---------------------------------------------------------
# REDIRECT URL TO SHAREPOINT FOLDER
# ---------------------------------------------------------

@router.get("/folder-url")
def get_sharepoint_folder_url(
    progetto_id: int,
    data_creazione: str,
    fornitore_nome: str,
    folder_type: str,
):
    token = get_access_token()
    site_id = get_site_id(token)
    drive_id = get_drive_id(token, site_id)

    project = find_project_folder_by_id(
        progetto_id=progetto_id,
        token=token,
        data_creazione=data_creazione,
        drive_id=drive_id,
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found in SharePoint",
        )

    # Find supplier inside project
    url = f"{GRAPH_URL}/drives/{drive_id}" f"/items/{project['id']}/children"

    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()

    supplier = next(
        (
            item
            for item in response.json().get("value", [])
            if item.get("folder") and item["name"] == fornitore_nome
        ),
        None,
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail=f"Supplier folder '{fornitore_nome}' not found",
        )

    # Find Ordine / Conferma Ordine
    response = requests.get(
        f"{GRAPH_URL}/drives/{drive_id}/items/{supplier['id']}/children",
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()

    folder = next(
        (
            item
            for item in response.json().get("value", [])
            if item.get("folder") and item["name"] == folder_type
        ),
        None,
    )

    if not folder:
        raise HTTPException(
            status_code=404,
            detail=f"Folder '{folder_type}' not found",
        )

    return {"web_url": folder["webUrl"]}


# =====================================================
# SYNC DATI CANTIERE OF A MONTH -> 06-Progetti/{year}/Dati Cantiere
# =====================================================


def list_folder_children(url: str, token: str) -> list[dict] | None:
    """All children of a drive folder (follows paging). None if the folder doesn't exist."""
    headers = {"Authorization": f"Bearer {token}"}
    items = []

    while url:
        response = requests.get(url, headers=headers)

        if response.status_code == 404:
            return None

        if not response.ok:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Could not list SharePoint folder: {response.text}",
            )

        data = response.json()
        items.extend(data.get("value", []))
        url = data.get("@odata.nextLink")

    return items


def list_files_recursive(folder_id: str, token: str, drive_id: str, rel_path: str = "") -> list[dict]:
    """Files inside a folder and its subfolders, with their path relative to the folder."""
    children = list_folder_children(
        f"{GRAPH_URL}/drives/{drive_id}/items/{folder_id}/children?$top=999", token
    ) or []

    files = []
    for item in children:
        name = item.get("name", "")
        item_rel_path = f"{rel_path}/{name}" if rel_path else name

        if "folder" in item:
            files.extend(list_files_recursive(item["id"], token, drive_id, item_rel_path))
        elif "file" in item:
            files.append({**item, "rel_path": item_rel_path})

    return files


@router.post("/sync-dati-cantiere")
def sync_dati_cantiere(
    year: int,
    month: int,
    dry_run: bool = True,
):
    """
    Copy every file found in 06-Progetti/{year}/{MM - Mon}/{progetto}/Dati Cantiere
    (subfolders included) to 06-Progetti/{year}/Dati Cantiere.

    The destination name is prefixed with the project folder name
    ({progetto_id}_{cliente_nome}_{file}), same as the automatic copy done by
    /upload-project, so files with the same name (e.g. dati-cantiere.json) coming
    from different projects don't overwrite each other.
    Files from subfolders keep the subfolder in the name ({progetto}_{sub}_{file}).

    Files already in the destination with the same name and size are skipped.
    dry_run=true (default) only lists what would be copied, nothing is written.
    """
    if not 1 <= month <= 12:
        raise HTTPException(status_code=400, detail="month must be 1-12")

    token = get_access_token()
    site_id = get_site_id(token)
    drive_id = get_drive_id(token, site_id)

    def path_url(path: str) -> str:
        return f"{GRAPH_URL}/drives/{drive_id}/root:/{quote(path, safe='/')}:/children?$top=999"

    year_path = f"06-Progetti/{year}"

    # Month folder: match by number ("10 - Oct"), so names like "03- Mar" are found too
    year_children = list_folder_children(path_url(year_path), token)
    if year_children is None:
        raise HTTPException(status_code=404, detail=f"Folder not found: {year_path}")

    month_prefix = f"{month:02d}"
    month_folder = next(
        (
            item for item in year_children
            if "folder" in item and item.get("name", "").strip().startswith(month_prefix)
        ),
        None,
    )
    if not month_folder:
        raise HTTPException(
            status_code=404,
            detail=f"Month folder {month_prefix} not found in {year_path}",
        )

    month_path = f"{year_path}/{month_folder['name']}"
    dest_path = f"{year_path}/{DATI_CANTIERE_FOLDER_NAME}"

    # Files already in the destination: name (lowercase) -> size
    dest_children = list_folder_children(path_url(dest_path), token) or []
    dest_files = {
        item.get("name", "").lower(): item.get("size")
        for item in dest_children
        if "file" in item
    }

    project_folders = [
        item for item in (list_folder_children(path_url(month_path), token) or [])
        if "folder" in item
    ]

    results = []
    projects_without_dati_cantiere = []

    def record(status: str, source: str, destination: str, detail=None):
        entry = {"source": source, "destination": destination, "status": status}
        if detail is not None:
            entry["detail"] = detail
        results.append(entry)
        print(
            f"[sync-dati-cantiere] {len(results)} {status.upper()}: {source} -> {destination}"
            + (f" | {detail}" if detail is not None else ""),
            flush=True,
        )

    for project in sorted(project_folders, key=lambda p: p.get("name", "")):
        project_name = project.get("name", "")

        # "Dati Cantiere" subfolder of the project (case-insensitive), if any
        dati_cantiere_folder = next(
            (
                item for item in (list_folder_children(
                    f"{GRAPH_URL}/drives/{drive_id}/items/{project['id']}/children?$top=999",
                    token,
                ) or [])
                if "folder" in item
                and item.get("name", "").strip().lower() == DATI_CANTIERE_FOLDER_NAME.lower()
            ),
            None,
        )
        if not dati_cantiere_folder:
            projects_without_dati_cantiere.append(project_name)
            continue

        files = list_files_recursive(dati_cantiere_folder["id"], token, drive_id)

        for f in files:
            dest_name = f"{project_name}_{f['rel_path'].replace('/', '_')}"
            source = f"{month_path}/{project_name}/{DATI_CANTIERE_FOLDER_NAME}/{f['rel_path']}"
            destination = f"{dest_path}/{dest_name}"

            if dest_files.get(dest_name.lower()) == f.get("size"):
                record("already_present", source, destination)
                continue

            if dry_run:
                record("would_copy", source, destination)
                continue

            try:
                download = requests.get(
                    f"{GRAPH_URL}/drives/{drive_id}/items/{f['id']}/content",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if not download.ok:
                    raise HTTPException(status_code=download.status_code, detail=download.text)

                upload = requests.put(
                    f"{GRAPH_URL}/drives/{drive_id}/root:/{quote(destination, safe='/')}:/content",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/octet-stream",
                    },
                    data=download.content,
                )
                if not upload.ok:
                    raise HTTPException(status_code=upload.status_code, detail=upload.text)

                dest_files[dest_name.lower()] = f.get("size")
                record("copied", source, destination)

            except HTTPException as e:
                record("error", source, destination, e.detail)

    def count(status: str) -> int:
        return sum(1 for r in results if r["status"] == status)

    return {
        "dry_run": dry_run,
        "month_folder": month_path,
        "destination_folder": dest_path,
        "projects_checked": len(project_folders),
        "projects_without_dati_cantiere": projects_without_dati_cantiere,
        "files_found": len(results),
        "would_copy": count("would_copy"),
        "copied": count("copied"),
        "already_present": count("already_present"),
        "errors": count("error"),
        "files": results,
    }
