import sys
import os
from fastapi import FastAPI, Depends
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, create_engine, Session, select
from contextlib import asynccontextmanager
from typing import List
import logging

if os.getenv("GITHUB_ACTIONS"):sys.path.append(os.path.dirname(__file__)) 
from routers import items  
from models.items import Item

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Define the Hero model
class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    superpower: str

# Create the PostgreSQL database and engine
rds_postgresql_url = "postgresql://rootuser:diocane1234@fastapi-aws-database.cjo4ss2ailsb.eu-north-1.rds.amazonaws.com:5432/postgres"
engine = create_engine(rds_postgresql_url, echo=True)

# Initialize the database
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


# Initialize the database
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


app = FastAPI(lifespan=lifespan)
handler = Mangum(app=app)

# CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()  # ✅ Runs only when the app starts
    yield

# Items Routers
app.include_router(
    items.router, 
    prefix="/items", 
    tags=["Items"]
)



@app.get("/")
async def root():
    return {"message": "Hello asdasd"}


# Endpoint to create a hero
@app.post("/heroes/", response_model=Hero)
def create_hero(hero: Hero):
    with Session(engine) as session:
        session.add(hero)
        session.commit()
        session.refresh(hero)
        return hero
    
@app.get("/test-db-connection")
def test_db():
    try:
        with Session(engine) as session:
            session.exec("SELECT 1")  # Simple test query
            return {"message": "Database connection successful"}
    except Exception as e:
        logger.error(f"Database connection failed: {e}", exc_info=True)
        return {"error": str(e)}

# Endpoint to get all heroes
@app.get("/heroes/", response_model=List[Hero])
def read_heroes():
    logger.info("Attempting to connect to DB...")
    with Session(engine) as session:
        logger.info('here')
        heroes = session.exec(select(Hero)).all()
        logger.info(f"Retrieved {len(heroes)} heroes from DB")
        return heroes

# # Endpoint to create an item
# @app.post("/items/", response_model=Item)
# def create_item(item: Item, db: Session = Depends(get_db)):
#     db.add(item)
#     db.commit()
#     db.refresh(item)
#     return item

# # Endpoint to get all items
# @app.get("/items/", response_model=List[Item])
# def read_items(db: Session = Depends(get_db)):
#     items = db.exec(select(Item)).all()
#     return items
