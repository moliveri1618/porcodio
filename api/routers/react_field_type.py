from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from models.react_field_type import ReactFieldType
from schemas.react_field_type import (
    ReactFieldTypeCreate,
    ReactFieldTypeRead,
    ReactFieldTypeUpdate,
)
from dependecies import get_db

router = APIRouter()


@router.post("", response_model=ReactFieldTypeRead, status_code=201)
def create_react_field_type(
    react_field_type: ReactFieldTypeCreate,
    db: Session = Depends(get_db),
):
    db_react_field_type = ReactFieldType(**react_field_type.dict())
    db.add(db_react_field_type)
    db.commit()
    db.refresh(db_react_field_type)
    return db_react_field_type


@router.get("", response_model=list[ReactFieldTypeRead])
def read_react_field_types(db: Session = Depends(get_db)):
    return db.exec(select(ReactFieldType)).all()


@router.get("/{react_field_type_id}", response_model=ReactFieldTypeRead)
def read_react_field_type(
    react_field_type_id: int,
    db: Session = Depends(get_db),
):
    db_react_field_type = db.get(ReactFieldType, react_field_type_id)

    if not db_react_field_type:
        raise HTTPException(status_code=404, detail="React field type not found")

    return db_react_field_type


@router.put("/{react_field_type_id}", response_model=ReactFieldTypeRead)
def update_react_field_type(
    react_field_type_id: int,
    react_field_type: ReactFieldTypeUpdate,
    db: Session = Depends(get_db),
):
    db_react_field_type = db.get(ReactFieldType, react_field_type_id)

    if not db_react_field_type:
        raise HTTPException(status_code=404, detail="React field type not found")

    update_data = react_field_type.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_react_field_type, key, value)

    db.add(db_react_field_type)
    db.commit()
    db.refresh(db_react_field_type)

    return db_react_field_type


@router.delete("/{react_field_type_id}")
def delete_react_field_type(
    react_field_type_id: int,
    db: Session = Depends(get_db),
):
    db_react_field_type = db.get(ReactFieldType, react_field_type_id)

    if not db_react_field_type:
        raise HTTPException(status_code=404, detail="React field type not found")

    db.delete(db_react_field_type)
    db.commit()

    return {"ok": True}
