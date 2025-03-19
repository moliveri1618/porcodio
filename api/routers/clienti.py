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

router = APIRouter()

# Create
@router.post("", response_model=ClienteRead)
def create_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    db_cliente = Cliente(**cliente.dict())  # Changed to Cliente model and dict() method
    db.add(db_cliente)
    db.commit()
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
