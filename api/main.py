from fastapi import FastAPI
from mangum import Mangum
import sys
import os
# Dynamically adjust the import path
if os.getenv("GITHUB_ACTIONS"):
    sys.path.append(os.path.dirname(__file__))  # Ensure current dir is in path

from routers import items  # Works both locally and in GitHub Actions

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
handler = Mangum(app=app)

# CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Items Routers
app.include_router(items.router, prefix="/items", tags=["Items"])

@app.get("/")
async def root():
    return {"message": "Hello asdasd"}
