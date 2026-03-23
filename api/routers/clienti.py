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



# ALLOWED_FIELDS_CLIENTE = ["centro_di_costo"]  # DO NOT CHANGE
# @router.put("/bulk/field", response_model=dict)
# def update_multiple_clienti_field(
#     field: str,
#     values: dict[str, List[str] | None],  # 👈 paste your dictionary here
#     db: Session = Depends(get_db),
# ):
#     # ✅ only allow whitelisted fields
#     if field not in ALLOWED_FIELDS_CLIENTE:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Field '{field}' is not allowed to be updated. Allowed fields: {ALLOWED_FIELDS_CLIENTE}"
#         )

#     updated, not_found = [], []

#     for cliente_id, value in values.items():
#         cliente = db.get(Cliente, cliente_id)
#         if not cliente:
#             not_found.append(cliente_id)
#             continue

#         try:
#             setattr(cliente, field, value)
#             db.add(cliente)
#             updated.append(cliente_id)
#         except AttributeError:
#             raise HTTPException(status_code=400, detail=f"Field '{field}' not found on model")

#     db.commit()

#     return {"updated": updated, "not_found": not_found}