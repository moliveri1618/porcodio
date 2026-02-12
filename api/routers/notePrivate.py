from fastapi import APIRouter, Depends, HTTPException
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

# @router.post("", response_model=NotePrivateRead, status_code=201)
# def create_note(note: NotePrivateCreate, db: Session = Depends(get_db)):
#     data = note.dict()
#     data["username"] = data["username"].strip().lower()

#     db_note = NotePrivate(**data)
#     db.add(db_note)
#     db.commit()
#     db.refresh(db_note)
#     return db_note


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
