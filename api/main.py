from fastapi import FastAPI
from mangum import Mangum
import sys
import os
from fastapi.middleware.cors import CORSMiddleware

if os.getenv("GITHUB_ACTIONS"):sys.path.append(os.path.dirname(__file__)) 
from routers import items  # Works both locally and in GitHub Actions


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
app.include_router(items.router, prefix="/items", tags=["Items"])

@app.get("/")
async def root():
    return {"message": "Hello asdasd"}
