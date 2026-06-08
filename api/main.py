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
from routers import (
    progetti,
    clienti,
    fornitori,
    progetto_fornitore_link,
    getFiles,
    prodotti,
    notePrivate,
    img_S3,
    progetti_parsing,
    tipo_prodotto,
    tipo_prodotto_valori,
    tipo_prodotto_dropdown,
    scheda_tecnica_pezzo,
    scheda_tecnica_schema
)

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
    progetti_parsing.router, 
    prefix="/progetti-parsing", 
    tags=["progetti-parsing"]
)

app.include_router(
    tipo_prodotto.router,
    prefix="/tipo-prodotto",
    tags=["tipo-prodotto"]
)

app.include_router(
    tipo_prodotto_valori.router,
    prefix="/tipo-prodotto-valori",
    tags=["tipo-prodotto-valori"]
)

app.include_router(
    tipo_prodotto_dropdown.router,
    prefix="/tipo-prodotto-dropdown",
    tags=["tipo-prodotto-dropdown"]
)

app.include_router(
    scheda_tecnica_schema.router,
    prefix="/scheda-tecnica-schema",
    tags=["scheda-tecnica-schema"]
)

app.include_router(
    scheda_tecnica_pezzo.router,
    prefix="/scheda-tecnica-pezzo",
    tags=["scheda-tecnica-pezzo"]
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

app.include_router(
    img_S3.router,
    prefix="/img_S3",
    tags=["img_S3"]
)

@app.get("/")
def root():
    return {"message": "FastAPI test client is running"}


# #############################################
# ########## Generate PRE Signed URL ##########
# ########## Upload  ------ Download ##########
# #############################################


# @app.get("/presign-upload")
# async def presign_upload(
#     key: str,
#     expires: int = 60,
#     content_type: str | None = None,
#     # current_user: dict = Depends(verify_cognito_token),
# ):
#     """
#     Generate a pre-signed URL for uploading a file (HTTP PUT) directly to S3.
#     Example:
#       GET /presign-upload?key=Gestionale/Fornitori/file.pdf&expires=60&content_type=application/pdf
#     Client then PUTs the file bytes to the returned URL.
#     """
#     if not _is_allowed_key(key):
#         raise HTTPException(status_code=400, detail="Key not allowed")

#     params = {
#         "Bucket": AWS_BUCKET,
#         "Key": key,
#     }
#     # Encourage clients to send the same Content-Type they’ll use in the PUT request
#     if content_type:
#         params["ContentType"] = content_type

#     try:
#         url = s3_client.generate_presigned_url(
#             ClientMethod="put_object",
#             Params=params,
#             ExpiresIn=_cap_expires(expires),
#         )
#         return {
#             "url": url,
#             "method": "PUT",
#             "key": key,
#             "expires_in": _cap_expires(expires),
#             "headers": {"Content-Type": content_type} if content_type else {},
#         }
#     except ClientError as e:
#         logger.error(f"Presign upload failed for {key}: {e}")
#         raise HTTPException(
#             status_code=500, detail="Failed to generate pre-signed upload URL"
#         )


# @app.get("/presign-download")
# async def presign_download(
#     key: str,
#     expires: int = 60,
#     download_name: str | None = None,
#     # current_user: dict = Depends(verify_cognito_token),
# ):
#     """
#     Generate a pre-signed URL for downloading a file (HTTP GET) from S3.
#     Example:
#       GET /presign-download?key=Gestionale/Emails/A.pdf&expires=60&download_name=Allegato.pdf
#     """
#     if not _is_allowed_key(key):
#         raise HTTPException(status_code=400, detail="Key not allowed")

#     params = {
#         "Bucket": AWS_BUCKET,
#         "Key": key,
#     }
#     if download_name:
#         params["ResponseContentDisposition"] = f'attachment; filename="{download_name}"'

#     try:
#         url = s3_client.generate_presigned_url(
#             ClientMethod="get_object",
#             Params=params,
#             ExpiresIn=_cap_expires(expires),
#         )
#         return {
#             "url": url,
#             "method": "GET",
#             "key": key,
#             "expires_in": _cap_expires(expires),
#         }
#     except ClientError as e:
#         logger.error(f"Presign download failed for {key}: {e}")
#         raise HTTPException(
#             status_code=500, detail="Failed to generate pre-signed download URL"
#         )


# @app.delete("/delete-file")
# async def delete_file(
#     key: str,
#     # current_user: dict = Depends(verify_cognito_token),
# ):
#     """
#     Delete a file directly from S3 (no pre-signed URL needed)
#     """
#     if not _is_allowed_key(key):
#         raise HTTPException(status_code=400, detail="Key not allowed")

#     try:
#         s3_client.delete_object(Bucket=AWS_BUCKET, Key=key)
#         return {
#             "success": True,
#             "message": f"File {key} deleted successfully",
#             "key": key,
#         }
#     except ClientError as e:
#         logger.error(f"Delete failed for {key}: {e}")
#         raise HTTPException(status_code=500, detail="Failed to delete file")


# # --- end block ----------------------------------------------------------------
