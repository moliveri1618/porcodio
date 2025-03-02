# Defines api routes and endpoints related to items
from fastapi import APIRouter, Depends
import sys
import os
from typing import List
from sqlmodel import Session, select

if os.getenv("GITHUB_ACTIONS"):sys.path.append(os.path.dirname(__file__)) 
from models.items import Item
from dependecies import get_db



router = APIRouter()

# Endpoint to create an item
@router.post("", response_model=Item)
def create_item(item: Item, db: Session = Depends(get_db)):
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

# Endpoint to get all items
@router.get("", response_model=List[Item])
def read_items(db: Session = Depends(get_db)):
    items = db.exec(select(Item)).all()
    return items
