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


# @router.put("/{item_id}", response_model=Item)
# def update_item(item_id: int, item: Item, db: Session = Depends(get_db)):
#     db_item = db.get(Item, item_id)  # Fetch the existing item
#     if not db_item:
#         raise HTTPException(status_code=404, detail="Item not found")

#     for key, value in item.dict().items():
#         setattr(db_item, key, value)  # Dynamically update fields

#     db.add(db_item)
#     db.commit()
#     db.refresh(db_item)
#     return db_item


# @router.delete("/{item_id}", response_model=Item)
# def delete_item(item_id: int, db: Session = Depends(get_db)):
#     db_item = db.get(Item, item_id)
#     if not db_item:
#         raise HTTPException(status_code=404, detail="Item not found")

#     db.delete(db_item)
#     db.commit()
#     return db_item  # Returning the deleted item is optional