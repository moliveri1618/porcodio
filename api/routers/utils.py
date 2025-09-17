
# utils/gesty.py

import httpx
from fastapi import HTTPException

API_BASE = "https://www.tigulliocrm.it/api"
API_KEY = "xAe5xrokrKL4g7sbyGHQ3mZ9wyqUVks7"
BASE_URL = "https://fsvejdikpdhubuz3kxl7w3koiq0iyvyj.lambda-url.eu-north-1.on.aws".rstrip("/")

def fetch_from_gesty(endpoint: str) -> dict:
    """
    Fetch data from Gesty API with Bearer token authentication.
    Raises HTTPException on error.
    """
    if not API_BASE or not API_KEY:
        raise HTTPException(status_code=500, detail="API_BASE/API_KEY not configured")

    headers = {"Authorization": f"Bearer {API_KEY}"}
    url = f"{API_BASE}/{endpoint.strip('/')}/"

    try:
        resp = httpx.get(url, headers=headers)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gesty fetch error: {e}")

    if resp.status_code != 200:
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        raise HTTPException(status_code=resp.status_code, detail={"upstream": body})

    payload = resp.json()
    if not payload.get("success"):
        raise HTTPException(status_code=502, detail="Gesty returned success=false")

    return payload['data'] if 'data' in payload else payload


def extract_prodotti_names(gesty_payload: dict) -> set[str]:
    """
    Traverse the Gesty payload and collect all product names.
    Expected structure: data -> list of items -> Progetto -> fornitori (dict) -> each has 'prodotti' list with 'prodotto'
    """
    names: set[str] = set()
    data = gesty_payload.get("data") or []
    for item in data:
        progetto = (item or {}).get("Progetto") or {}
        fornitori = progetto.get("fornitori") or {}
        for _, forn in fornitori.items():
            for prod in (forn or {}).get("prodotti") or []:
                name = (prod or {}).get("prodotto")
                if isinstance(name, str):
                    # normalize: strip extra spaces; keep original casing otherwise
                    clean = name.strip()
                    if clean:
                        names.add(clean)
    return names

def attach_file_links(payload: list[dict]) -> list[dict]:
    """
    Replace contratto_code and rm_code with proxy URLs if present.
    """
    for item in payload:
        progetto = item.get("Progetto") or {}

        contratto_code = progetto.get("contratto_code")
        if contratto_code and isinstance(contratto_code, str) and contratto_code.strip():
            progetto["contratto_code"] = f"{BASE_URL}/getFiles/contratto/{contratto_code}"

        rm_code = progetto.get("rm_code")
        if rm_code and isinstance(rm_code, str) and rm_code.strip():
            progetto["rm_code"] = f"{BASE_URL}/getFiles/rm/{rm_code}"

    return payload