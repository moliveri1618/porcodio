import sys
import os
from fastapi import FastAPI, Depends
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, create_engine, Session
from contextlib import asynccontextmanager

if os.getenv("GITHUB_ACTIONS"):sys.path.append(os.path.dirname(__file__)) 
from routers import items  
from models.items import Item

# Create the PostgreSQL database and engine
rds_postgresql_url = "postgresql://rootuser:password@fastapi-aws-database.cjo4ss2ailsb.eu-north-1.rds.amazonaws.com:5432/postgres"
engine = create_engine(rds_postgresql_url, echo=True)

# Initialize the database
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()  # ✅ Runs only when the app starts
    yield

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

# Items Routers
app.include_router(
    items.router, 
    prefix="/items", 
    tags=["Items"]
)

@app.get("/")
async def root():
    return {"message": "Hello asdasd"}

# Endpoint to create an item
@app.post("/items/", response_model=Item)
def create_item(item: Item, db: Session = Depends(get_db)):
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

# Endpoint to get all items
@app.get("/items/", response_model=List[Item])
def read_items(db: Session = Depends(get_db)):
    items = db.exec(select(Item)).all()
    return items
