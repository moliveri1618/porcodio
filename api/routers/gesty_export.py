# External API for Gesty: rilievo misure date, tecnico and note of each project.
# Separate router with its own Bearer token (env GESTY_API_TOKEN), hidden from /docs.
import hmac
import os
import sys
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlmodel import Session

if os.getenv("GITHUB_ACTIONS"):
    sys.path.append(os.path.dirname(__file__))

from dependecies import get_db
from models.progetti import Progetti

router = APIRouter()

_bearer = HTTPBearer(auto_error=False)


def verify_gesty_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> None:
    expected = os.getenv("GESTY_API_TOKEN")
    if not expected:
        # fail closed: never serve data if the token is not configured
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API not configured",
        )
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not hmac.compare_digest(
            credentials.credentials.encode(), expected.encode()
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/progetti", dependencies=[Depends(verify_gesty_token)])
def get_progetti_gesty(
    progetto_id: Optional[str] = Query(
        None, description="Gesty project id: return only this project"
    ),
    db: Session = Depends(get_db),
):
    """
    For every project imported from Gesty (progetto_id set):
    data_rilievo_misure (first Rilievo Misure upload), tecnico, note.
    Single query on the needed columns only, no ORM objects, no joins.
    """
    stmt = select(
        Progetti.id,
        Progetti.progetto_id,
        Progetti.data_rilievo_misure,
        Progetti.tecnico,
        Progetti.note,
    ).where(func.coalesce(func.trim(Progetti.progetto_id), "") != "")

    if progetto_id and progetto_id.strip():
        stmt = stmt.where(Progetti.progetto_id == progetto_id.strip())

    stmt = stmt.order_by(Progetti.id)

    rows = db.execute(stmt).all()

    items = [
        {
            "id": row.id,
            "progetto_id": row.progetto_id,
            "data_rilievo_misure": (
                row.data_rilievo_misure.isoformat()
                if row.data_rilievo_misure
                else None
            ),
            "tecnico": (row.tecnico or "").strip() or None,
            "note": row.note or None,
        }
        for row in rows
    ]

    return {"total": len(items), "items": items}
