# Defines api routes and endpoints related to items
from fastapi import APIRouter, Depends
import sys
import os
from typing import List
from sqlmodel import Session, select

if os.getenv("GITHUB_ACTIONS"):sys.path.append(os.path.dirname(__file__)) 
from models.items import Item
from schemas.items import ItemCreate, ItemRead
from dependecies import get_db


router = APIRouter()

# Endpoint to create an item
@router.post("", response_model=ItemRead)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# Endpoint to get all items
@router.get("", response_model=List[ItemRead])
def read_items(db: Session = Depends(get_db)):
    items = db.exec(select(Item)).all()
    return items