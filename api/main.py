import sys
import os
from fastapi import FastAPI, Depends, Request, HTTPException
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import httpx, io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi.responses import StreamingResponse, JSONResponse


if os.getenv("GITHUB_ACTIONS"):sys.path.append(os.path.dirname(__file__)) 
from routers import progetti, clienti, fornitori, progetto_fornitore_link, getFiles, prodotti, notePrivate
# from routers import clienti
# from routers import fornitori
# from routers import progetto_fornitore_link
# from routers import getFiles
from dependecies import create_db_and_tables, verify_cognito_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(create_db_and_tables)
    yield

app = FastAPI(lifespan=lifespan)
handler = Mangum(app=app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://staging.d1z7mkjg7hq21f.amplifyapp.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], 
    allow_headers=["Content-Type", "Authorization"], 
)

app.include_router(
    progetti.router, 
    prefix="/progetti", 
    tags=["progetti"]
)

app.include_router(
    clienti.router, 
    prefix="/clienti", 
    tags=["clienti"]
)

app.include_router(
    fornitori.router, 
    prefix="/fornitori", 
    tags=["fornitori"]
)

app.include_router(
    progetto_fornitore_link.router, 
    prefix="/progetti-fornitori", 
    tags=["progetti-fornitori"]
)

app.include_router(
    getFiles.router, 
    prefix="/getFiles", 
    tags=["getFiles"]
)

app.include_router(
    prodotti.router, 
    prefix="/prodotti", 
    tags=["prodotti"]
)

app.include_router(
    notePrivate.router, 
    prefix="/notePrivate", 
    tags=["notePrivate"]
)


@app.get("/")
async def root(current_user: dict = Depends(verify_cognito_token)):
    return {"message": "Hello"}

@app.get("/")
def root():
    return {"message": "FastAPI test client is running"}



    

