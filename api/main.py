import sys
import os
from fastapi import FastAPI, Depends
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, create_engine, Session, select
from contextlib import asynccontextmanager
from typing import List
import logging
from sqlalchemy import text  # Import SQLAlchemy's text() function

if os.getenv("GITHUB_ACTIONS"):sys.path.append(os.path.dirname(__file__)) 
from routers import items  
from models.items import Item
from sqlalchemy import text  
from dependecies import get_db, create_db_and_tables, engine


logger = logging.getLogger()
logger.setLevel(logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
handler = Mangum(app=app)

# CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (adjust as needed)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly define allowed methods
    allow_headers=["Content-Type", "Authorization"],  # Define allowed headers
)


# Items Routers
app.include_router(
    items.router, 
    prefix="/items", 
    tags=["Items"]
)


@app.get("/")
async def root():
    return {"message": "Hello asdasd"}



# # Define the Hero model
# class Hero(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True)
#     name: str
#     superpower: str

# Endpoint to create a hero
# @app.post("/heroes", response_model=Hero)
# def create_hero(hero: Hero):
#     with Session(engine) as session:
#         session.add(hero)
#         session.commit()
#         session.refresh(hero)
#         return hero
    

# # Endpoint to get all heroes
# @app.get("/heroes", response_model=List[Hero])
# def read_heroes():
#     logger.info("Attemptingdd to connect to DB...")
#     with Session(engine) as session:
#         logger.info('here')
#         heroes = session.exec(select(Hero)).all()
#         logger.info(f"Retrieved {len(heroes)} heroes from DB")
#         return heroes

    