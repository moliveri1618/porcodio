import sys
import os
from fastapi import FastAPI, Depends
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

if os.getenv("GITHUB_ACTIONS"):sys.path.append(os.path.dirname(__file__)) 
from routers import items  
from dependecies import create_db_and_tables, verify_cognito_token


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
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], 
    allow_headers=["Content-Type", "Authorization"], 
)


# Items Routers
app.include_router(
    items.router, 
    prefix="/items", 
    tags=["Items"]
)


@app.get("/")
async def root():
    import requests

    try:
        response = requests.get("https://www.google.com", timeout=5)
        return {"status": response.status_code, "body": response.text[:200]}  # Return first 200 chars
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    return {"message": "Hello"}



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

# Create the PostgreSQL database and engine
#rds_postgresql_url = "postgresql://rootuser:diocane1234@database-fastapi-aws.cjo4ss2ailsb.eu-north-1.rds.amazonaws.com:5432/postgres"
#rds_postgresql_url = "postgresql://postgres:password@localhost:5432/PCS_micro"