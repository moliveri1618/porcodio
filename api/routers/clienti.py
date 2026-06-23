# Defines API routes and endpoints related to cliente

from fastapi import APIRouter, Depends, HTTPException
import sys
import os
from typing import List
from sqlmodel import Session, select

if os.getenv("GITHUB_ACTIONS"): sys.path.append(os.path.dirname(__file__)) 
from models.clienti import Cliente  # Changed model name from Progetti to Cliente
from schemas.clienti import ClienteCreate, ClienteRead, ClienteUpdate  # Updated schemas
from dependecies import get_db
from routers.utils import fetch_from_gesty

router = APIRouter()


# Get from gesty
@router.get("/match_clienti_data_with_gesty")
def fix_clienti_data_with_gesty(db: Session = Depends(get_db)):

    payload = fetch_from_gesty("dip-tecnico")

    if isinstance(payload, dict):
        data = payload.get("data", [])
    elif isinstance(payload, list):
        data = payload
    else:
        data = []

    updated_clients = 0
    skipped_clients = 0

    for item in data:
        cliente_data = item.get("Cliente", {})

        if not cliente_data.get("id"):
            continue

        cliente_id = int(cliente_data["id"])

        existing_cliente = db.get(Cliente, cliente_id)

        if not existing_cliente:
            skipped_clients += 1
            continue

        # UPDATE ONLY THESE FIELDS
        existing_cliente.nome_cliente = (
            cliente_data.get("nome_cliente") or existing_cliente.nome_cliente
        )

        existing_cliente.citta = cliente_data.get("citta") or existing_cliente.citta

        existing_cliente.indirizzo = (
            cliente_data.get("indirizzo") or existing_cliente.indirizzo
        )

        existing_cliente.numero_tel = (
            cliente_data.get("numero_tel") or existing_cliente.numero_tel
        )

        existing_cliente.email = cliente_data.get("email") or existing_cliente.email

        updated_clients += 1

    db.commit()

    return {
        "success": True,
        "updated_clients": updated_clients,
        "skipped_clients": skipped_clients,
        "total_payload_clients": len(data),
    }


# Create
@router.post("", response_model=ClienteRead)
def create_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    
    
    
    # Always ensure we have an ID before creating the object
    cliente_data = cliente.dict(exclude_unset=True)
    if not cliente_data.get('id') or cliente_data.get('id') == '':
        last_cliente = db.query(Cliente).order_by(Cliente.id.desc()).first()
        
        if last_cliente and last_cliente.id:
            try:
                last_num = int(last_cliente.id)
                cliente_data['id'] = str(last_num + 1)
            except ValueError:
                raise HTTPException(status_code=400, detail="Cannot auto-generate ID: last ID is not numeric")
        else:
            cliente_data['id'] = '1'
            
    
            
            
    db_cliente = Cliente(**cliente_data)
    db.add(db_cliente)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error inserting cliente: {str(e)}")
    db.refresh(db_cliente)
    return db_cliente

# Get all
@router.get("", response_model=List[ClienteRead])
def read_clienti(db: Session = Depends(get_db)):
    clienti = db.exec(select(Cliente)).all()  # Using Cliente model to fetch all records
    return clienti

# Get one
@router.get("/{cliente_id}", response_model=ClienteRead)
def read_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, cliente_id)  # Fetching a specific Cliente record by ID
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente not found")
    return cliente

# Put
@router.put("/{cliente_id}", response_model=ClienteRead)
def update_cliente(cliente_id: int, cliente_update: ClienteUpdate, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, cliente_id)  # Fetch the cliente to update
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente not found")
    cliente_data = cliente_update.dict(exclude_unset=True)  # Changed to dict() method
    for key, value in cliente_data.items():
        setattr(cliente, key, value)  # Update the cliente with new values
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente

# Delete
@router.delete("/{cliente_id}", status_code=204)
def delete_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, cliente_id)  # Fetch cliente to delete
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente not found")
    db.delete(cliente)
    db.commit()
