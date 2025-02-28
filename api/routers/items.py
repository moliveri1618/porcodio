# Defines api routes and endpoints related to items
from fastapi import APIRouter

router = APIRouter()

@router.get("/diocane")
def get_items():
    return {"bgggg": "Hello, world! Itemsdd"}