from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
import sys
import os
import requests

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
