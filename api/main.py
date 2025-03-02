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

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     create_db_and_tables()
#     yield

app = FastAPI()
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
# async def root(current_user: dict = Depends(verify_cognito_token)):
async def root():
    import requests

    try:
        response = requests.get("https://www.google.com", timeout=5)
        return {"status": response.status_code, "body": response.text[:200]}  # Return first 200 chars
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    return {"message": "Hello"}