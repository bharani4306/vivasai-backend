from fastapi import APIRouter, HTTPException, Depends
from typing import List
from database import get_db_connection
from models.schemas import OwnerCreate, OwnerUpdate, OwnerResponse
from services.auth_service import get_current_user

router = APIRouter(prefix="/api/owners", tags=["Owners"])

@router.get("", response_model=List[OwnerResponse])
def get_all_owners(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, id as user_id, name, phone, address, land_size_acres, crop_type, created_at FROM owners ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("", response_model=OwnerResponse)
def create_owner(payload: OwnerCreate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM owners WHERE email = ? OR phone = ?", (payload.email, payload.phone))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Owner with this email or phone already exists")

    cursor.execute(
        "INSERT INTO owners (name, email, phone, password_hash, address, land_size_acres, crop_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (payload.name, payload.email, payload.phone, payload.password, payload.address, payload.land_size_acres, payload.crop_type)
    )
    owner_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT id, id as user_id, name, phone, address, land_size_acres, crop_type, created_at FROM owners WHERE id = ?", (owner_id,))
    row = dict(cursor.fetchone())
    conn.close()
    return row

@router.get("/{owner_id}", response_model=OwnerResponse)
def get_owner_by_id(owner_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, id as user_id, name, phone, address, land_size_acres, crop_type, created_at FROM owners WHERE id = ?", (owner_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Owner not found")
    return dict(row)

@router.put("/{owner_id}", response_model=OwnerResponse)
def update_owner(owner_id: int, payload: OwnerUpdate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    update_fields = []
    values = []
    if payload.name:
        update_fields.append("name = ?")
        values.append(payload.name)
    if payload.phone:
        update_fields.append("phone = ?")
        values.append(payload.phone)
    if payload.address:
        update_fields.append("address = ?")
        values.append(payload.address)
    if payload.land_size_acres is not None:
        update_fields.append("land_size_acres = ?")
        values.append(payload.land_size_acres)
    if payload.crop_type:
        update_fields.append("crop_type = ?")
        values.append(payload.crop_type)

    if update_fields:
        query = f"UPDATE owners SET {', '.join(update_fields)} WHERE id = ?"
        values.append(owner_id)
        cursor.execute(query, values)
        conn.commit()

    cursor.execute("SELECT id, id as user_id, name, phone, address, land_size_acres, crop_type, created_at FROM owners WHERE id = ?", (owner_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)

@router.delete("/{owner_id}")
def delete_owner(owner_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM owners WHERE id = ?", (owner_id,))
    conn.commit()
    conn.close()
    return {"message": "Owner deleted successfully"}
