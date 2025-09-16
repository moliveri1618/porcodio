


def _extract_prodotti_names(gesty_payload: dict) -> set[str]:
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
