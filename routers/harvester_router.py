from fastapi import APIRouter, HTTPException, Depends
from typing import List
from database import get_db_connection
from models.schemas import HarvesterCreate, HarvesterUpdate, HarvesterResponse
from services.auth_service import get_current_user

router = APIRouter(prefix="/api/harvesters", tags=["Harvesters Fleet"])

@router.get("", response_model=List[HarvesterResponse])
def get_all_harvesters(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM harvesters ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("", response_model=HarvesterResponse)
def add_harvester(payload: HarvesterCreate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM harvesters WHERE registration_number = ?", (payload.registration_number,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Harvester registration number already exists")

    cursor.execute(
        """INSERT INTO harvesters (model_name, registration_number, type, hourly_rate, location, capacity, status) 
           VALUES (?, ?, ?, ?, ?, ?, 'available')""",
        (payload.model_name, payload.registration_number, payload.type, payload.hourly_rate, payload.location, payload.capacity)
    )
    conn.commit()
    hid = cursor.lastrowid
    cursor.execute("SELECT * FROM harvesters WHERE id = ?", (hid,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)

@router.get("/{harvester_id}", response_model=HarvesterResponse)
def get_harvester_by_id(harvester_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM harvesters WHERE id = ?", (harvester_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Harvester not found")
    return dict(row)

@router.put("/{harvester_id}", response_model=HarvesterResponse)
def update_harvester(harvester_id: int, payload: HarvesterUpdate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    update_fields = []
    values = []
    if payload.model_name:
        update_fields.append("model_name = ?")
        values.append(payload.model_name)
    if payload.registration_number:
        update_fields.append("registration_number = ?")
        values.append(payload.registration_number)
    if payload.type:
        update_fields.append("type = ?")
        values.append(payload.type)
    if payload.hourly_rate is not None:
        update_fields.append("hourly_rate = ?")
        values.append(payload.hourly_rate)
    if payload.status:
        update_fields.append("status = ?")
        values.append(payload.status)
    if payload.location:
        update_fields.append("location = ?")
        values.append(payload.location)
    if payload.capacity:
        update_fields.append("capacity = ?")
        values.append(payload.capacity)

    if update_fields:
        query = f"UPDATE harvesters SET {', '.join(update_fields)} WHERE id = ?"
        values.append(harvester_id)
        cursor.execute(query, values)
        conn.commit()

    cursor.execute("SELECT * FROM harvesters WHERE id = ?", (harvester_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)

@router.delete("/{harvester_id}")
def delete_harvester(harvester_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM harvesters WHERE id = ?", (harvester_id,))
    conn.commit()
    conn.close()
    return {"message": "Harvester deleted from fleet"}
