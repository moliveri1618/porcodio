import sys
import os
from fastapi import FastAPI
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

if os.getenv("GITHUB_ACTIONS"):sys.path.append(os.path.dirname(__file__)) 
from routers import items  

# Create the PostgreSQL database and engine
rds_postgresql_url = "postgresql://rootuser:password@fastapi-aws-database.cjo4ss2ailsb.eu-north-1.rds.amazonaws.com:5432/postgres"
engine = create_engine(rds_postgresql_url, echo=True)

def test_db_connection():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))  # ✅ Use `text()`
        print("✅ Database connection successful!")
    except OperationalError as e:
        print("❌ Database connection failed:", str(e))

# Run this before initializing tables
test_db_connection()


app = FastAPI()
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
