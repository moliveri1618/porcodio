from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
import sys
import os
from typing import List
from sqlmodel import Session, select
from sqlalchemy import func

# Allow relative imports when running in GitHub Actions
if os.getenv("GITHUB_ACTIONS"):
    sys.path.append(os.path.dirname(__file__))

from models.notePrivate import NotePrivate
from schemas.notePrivate import NotePrivateCreate, NotePrivateRead, NotePrivateUpdate
from dependecies import get_db

router = APIRouter()

@router.post("", response_model=NotePrivateRead, status_code=201)
def create_update_note(note: NotePrivateCreate, db: Session = Depends(get_db)):
    data = note.dict()

    normalized_username = data["username"].strip().lower()
    data["username"] = normalized_username

    # case-insensitive lookup (safe even if older rows have mixed case)
    stmt = select(NotePrivate).where(func.lower(NotePrivate.username) == normalized_username)
    existing = db.exec(stmt).first()

    if existing:
        # update only the note field (and any other fields you want)
        existing.note = data.get("note", existing.note)
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    # create new
    db_note = NotePrivate(**data)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

# Get all (optional, but useful)
@router.get("", response_model=List[NotePrivateRead])
def read_notes(db: Session = Depends(get_db)):
    notes = db.exec(select(NotePrivate)).all()
    return notes

# Get by id
@router.get("/{note_id}", response_model=NotePrivateRead)
def read_note(note_id: int, db: Session = Depends(get_db)):
    note = db.get(NotePrivate, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

# Get by username (recommended for your UI)
@router.get("/by-username/{username}", response_model=List[NotePrivateRead])
def read_notes_by_username(username: str, db: Session = Depends(get_db)):
    stmt = select(NotePrivate).where(
        func.lower(NotePrivate.username) == username.lower()
    )
    return db.exec(stmt).all()

# Put (partial update supported via exclude_unset)
@router.put("/{note_id}", response_model=NotePrivateRead)
def update_note(note_id: int, note_update: NotePrivateUpdate, db: Session = Depends(get_db)):
    note = db.get(NotePrivate, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    update_data = note_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(note, key, value)

    db.add(note)
    db.commit()
    db.refresh(note)
    return note

# Put by username (nice if you want one note per user)
@router.put("/by-username/{username}", response_model=NotePrivateRead)
def upsert_note_by_username(username: str, note_update: NotePrivateUpdate, db: Session = Depends(get_db)):
    stmt = select(NotePrivate).where(NotePrivate.username == username)
    existing = db.exec(stmt).first()

    if existing:
        update_data = note_update.dict(exclude_unset=True)
        # ensure username remains consistent with path
        update_data.pop("username", None)
        for key, value in update_data.items():
            setattr(existing, key, value)
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    # if not found, create it
    note_text = note_update.note if note_update.note is not None else ""
    created = NotePrivate(username=username, note=note_text)
    db.add(created)
    db.commit()
    db.refresh(created)
    return created


import requests

import os

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
