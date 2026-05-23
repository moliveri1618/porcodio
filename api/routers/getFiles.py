# Defines API routes and endpoints related to progetti

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import httpx, io


router = APIRouter()

API_BASE = "https://www.tigulliocrm.it/api"
API_URL = "https://www.tigulliocrm.it/api/fornitori/"
API_KEY = "xAe5xrokrKL4g7sbyGHQ3mZ9wyqUVks7"


async def fetch_pdf_from_crm(tipo: str, code: str) -> bytes:
    url = f"{API_BASE}/{tipo}/{code}/"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, headers=headers)

    if r.status_code == 200:
        return r.content

    if r.status_code in (401, 403):
        raise HTTPException(status_code=401, detail="Token non valido")

    raise HTTPException(status_code=r.status_code, detail=r.text)


@router.get("/contratto/{code}", responses={
    200: {"content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}}},
    401: {"description": "Token non valido"},
})
async def get_contratto(code: str):
    url = f"{API_BASE}/contratto/{code}/"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, headers=headers)

    if r.status_code == 200:
        return StreamingResponse(
            io.BytesIO(r.content),
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="contratto-{code}.pdf"'}
        )

    if r.status_code in (401, 403):
        raise HTTPException(status_code=401, detail="Token non valido")

    raise HTTPException(status_code=r.status_code, detail=r.text)


@router.get("/rm/{code}", responses={
    200: {"content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}}},
    401: {"description": "Token non valido"},
})
async def get_rm(code: str):
    url = f"{API_BASE}/rm/{code}/"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, headers=headers)

    if r.status_code == 200:
        return StreamingResponse(
            io.BytesIO(r.content),
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="contratto-{code}.pdf"'}
        )

    if r.status_code in (401, 403):
        raise HTTPException(status_code=401, detail="Token non valido")

    raise HTTPException(status_code=r.status_code, detail=r.text)


@router.get("/contratto/{code}/download")
async def download_contratto(code: str):
    pdf_bytes = await fetch_pdf_from_crm("contratto", code)

    # pass pdf_bytes to your parser
    # parsed_data = your_parser_function(pdf_bytes)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="contratto-{code}.pdf"'},
    )
