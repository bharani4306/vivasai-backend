from fastapi import APIRouter, HTTPException, Depends
from typing import List
from database import get_db_connection
from models.schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from services.auth_service import get_current_user

router = APIRouter(prefix="/api/employees", tags=["Employees"])

@router.get("", response_model=List[EmployeeResponse])
def get_all_employees(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, id as user_id, name, phone, designation, machine_assigned, status, created_at FROM employees ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("", response_model=EmployeeResponse)
def create_employee(payload: EmployeeCreate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM employees WHERE email = ? OR phone = ?", (payload.email, payload.phone))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Employee with this email or phone already exists")

    cursor.execute(
        "INSERT INTO employees (name, email, phone, password_hash, designation, machine_assigned, status) VALUES (?, ?, ?, ?, ?, ?, 'available')",
        (payload.name, payload.email, payload.phone, payload.password, payload.designation, payload.machine_assigned)
    )
    employee_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT id, id as user_id, name, phone, designation, machine_assigned, status, created_at FROM employees WHERE id = ?", (employee_id,))
    row = dict(cursor.fetchone())
    conn.close()
    return row

@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee_by_id(employee_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, id as user_id, name, phone, designation, machine_assigned, status, created_at FROM employees WHERE id = ?", (employee_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")
    return dict(row)

@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: int, payload: EmployeeUpdate, current_user: dict = Depends(get_current_user)):
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
    if payload.designation:
        update_fields.append("designation = ?")
        values.append(payload.designation)
    if payload.machine_assigned:
        update_fields.append("machine_assigned = ?")
        values.append(payload.machine_assigned)
    if payload.status:
        update_fields.append("status = ?")
        values.append(payload.status)

    if update_fields:
        query = f"UPDATE employees SET {', '.join(update_fields)} WHERE id = ?"
        values.append(employee_id)
        cursor.execute(query, values)
        conn.commit()

    cursor.execute("SELECT id, id as user_id, name, phone, designation, machine_assigned, status, created_at FROM employees WHERE id = ?", (employee_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)

@router.delete("/{employee_id}")
def delete_employee(employee_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
    conn.commit()
    conn.close()
    return {"message": "Employee deleted successfully"}
