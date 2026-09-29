from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from database import get_db_connection
from models.schemas import (
    ServiceRequestCreate, ServiceRequestResponse, 
    VerifyAcceptOtpRequest, VerifyCompleteOtpRequest
)
from services.auth_service import get_current_user
from services.otp_service import create_and_store_otp, verify_otp_code
from services.email_service import notify_admin_new_service_request, notify_admin_service_completed

router = APIRouter(prefix="/api/service-requests", tags=["Service Requests Workflow"])

def _format_sr_row(conn, sr_id):
    cursor = conn.cursor()
    cursor.execute(
        """SELECT sr.*, 
                  o.name as owner_name, o.phone as owner_phone,
                  h.model_name as harvester_name, h.hourly_rate,
                  sa.employee_id, e.name as employee_name
           FROM service_requests sr
           JOIN owners o ON sr.owner_id = o.id
           JOIN harvesters h ON sr.harvester_id = h.id
           LEFT JOIN service_assignments sa ON sr.id = sa.service_request_id
           LEFT JOIN employees e ON sa.employee_id = e.id
           WHERE sr.id = ?""",
        (sr_id,)
    )
    r = cursor.fetchone()
    if not r:
        return None

    # Fetch Accept & Complete OTPs from otp_verifications
    cursor.execute(
        "SELECT otp_code FROM otp_verifications WHERE service_request_id = ? AND purpose = 'ACCEPT_SERVICE' ORDER BY id DESC LIMIT 1",
        (sr_id,)
    )
    accept_row = cursor.fetchone()
    accept_otp = accept_row["otp_code"] if accept_row else None

    cursor.execute(
        "SELECT otp_code FROM otp_verifications WHERE service_request_id = ? AND purpose = 'COMPLETE_SERVICE' ORDER BY id DESC LIMIT 1",
        (sr_id,)
    )
    complete_row = cursor.fetchone()
    complete_otp = complete_row["otp_code"] if complete_row else None

    return {
        "id": r["id"],
        "owner_id": r["owner_id"],
        "owner_name": r["owner_name"],
        "owner_phone": r["owner_phone"],
        "employee_id": r["employee_id"],
        "employee_name": r["employee_name"],
        "harvester_id": r["harvester_id"],
        "harvester_name": r["harvester_name"],
        "service_date": r["service_date"],
        "location": r["location"],
        "land_acres": r["land_acres"],
        "crop_type": r["crop_type"],
        "status": r["status"],
        "service_accept_otp": accept_otp,
        "service_complete_otp": complete_otp,
        "total_hours": r["total_hours"],
        "total_amount": r["total_amount"],
        "created_at": r["created_at"]
    }

@router.get("", response_model=List[ServiceRequestResponse])
def get_service_requests(
    owner_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT DISTINCT sr.id FROM service_requests sr LEFT JOIN service_assignments sa ON sr.id = sa.service_request_id WHERE 1=1"
    params = []

    if owner_id:
        query += " AND sr.owner_id = ?"
        params.append(owner_id)
    if employee_id:
        query += " AND sa.employee_id = ?"
        params.append(employee_id)
    if status:
        query += " AND sr.status = ?"
        params.append(status)

    query += " ORDER BY sr.id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    result = []
    for r in rows:
        formatted = _format_sr_row(conn, r["id"])
        if formatted:
            result.append(formatted)

    conn.close()
    return result

@router.post("", response_model=ServiceRequestResponse)
def create_service_request(payload: ServiceRequestCreate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify Owner
    cursor.execute("SELECT id, name, phone FROM owners WHERE id = ?", (payload.owner_id,))
    owner = cursor.fetchone()
    if not owner:
        conn.close()
        raise HTTPException(status_code=404, detail="Land Owner not found")

    # Verify Harvester
    cursor.execute("SELECT id, model_name, hourly_rate FROM harvesters WHERE id = ?", (payload.harvester_id,))
    harvester = cursor.fetchone()
    if not harvester:
        conn.close()
        raise HTTPException(status_code=404, detail="Harvester machine not found")

    estimated_hours = payload.land_acres * 1.5
    estimated_amount = estimated_hours * harvester["hourly_rate"]

    # Status: Waiting (Waiting for Admin assignment)
    cursor.execute(
        """INSERT INTO service_requests 
           (owner_id, harvester_id, service_date, location, land_acres, crop_type, status, total_hours, total_amount) 
           VALUES (?, ?, ?, ?, ?, ?, 'Waiting', 0.0, ?)""",
        (payload.owner_id, payload.harvester_id, payload.service_date, payload.location, payload.land_acres, payload.crop_type, estimated_amount)
    )
    sr_id = cursor.lastrowid
    conn.commit()

    # Auto-generate Accept OTP and Complete OTP on Owner side
    accept_otp = create_and_store_otp(sr_id, "ACCEPT_SERVICE")
    complete_otp = create_and_store_otp(sr_id, "COMPLETE_SERVICE")

    # Email Admin (vivasaiagencies@gmail.com)
    notify_admin_new_service_request(sr_id, owner["name"], payload.land_acres, harvester["model_name"])

    # Create Notification for Admin
    cursor.execute(
        "INSERT INTO notifications (user_id, user_role, title, message, type) VALUES (?, ?, ?, ?, ?)",
        (1, "admin", "New Booking Request", f"Owner {owner['name']} requested service #{sr_id} for {payload.land_acres} Acres.", "service")
    )

    # Create Notification for Owner with OTP
    cursor.execute(
        "INSERT INTO notifications (user_id, user_role, title, message, type) VALUES (?, ?, ?, ?, ?)",
        (payload.owner_id, "owner", "Service Booking Created", f"Service Request #{sr_id} created! Service Accept OTP: {accept_otp}, Complete OTP: {complete_otp}", "service")
    )
    conn.commit()

    formatted = _format_sr_row(conn, sr_id)
    conn.close()
    return formatted

@router.post("/{sr_id}/generate-otp")
def generate_otp_for_owner(sr_id: int, purpose: str = "ACCEPT_SERVICE", current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT owner_id FROM service_requests WHERE id = ?", (sr_id,))
    sr = cursor.fetchone()
    if not sr:
        conn.close()
        raise HTTPException(status_code=404, detail="Service request not found")

    new_otp = create_and_store_otp(sr_id, purpose)
    conn.close()
    return {"service_request_id": sr_id, "purpose": purpose, "otp_code": new_otp}

@router.post("/{sr_id}/assign-employee")
def assign_employee(sr_id: int, employee_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM service_requests WHERE id = ?", (sr_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Service request not found")

    cursor.execute("SELECT id, name FROM employees WHERE id = ?", (employee_id,))
    emp = cursor.fetchone()
    if not emp:
        conn.close()
        raise HTTPException(status_code=404, detail="Employee not found")

    cursor.execute(
        "INSERT INTO service_assignments (service_request_id, employee_id, assigned_by_admin_id, status) VALUES (?, ?, ?, 'Assigned')",
        (sr_id, employee_id, current_user["user_id"])
    )
    cursor.execute("UPDATE service_requests SET status = 'Assigned' WHERE id = ?", (sr_id,))
    conn.commit()

    cursor.execute(
        "INSERT INTO notifications (user_id, user_role, title, message, type) VALUES (?, ?, ?, ?, ?)",
        (employee_id, "employee", "New Field Job Assigned", f"Admin assigned you to Service Job #{sr_id}. Please accept task.", "service")
    )
    conn.commit()
    conn.close()

    return {"message": f"Employee {emp['name']} assigned to Service #{sr_id}"}

@router.post("/{sr_id}/accept-request")
def accept_request(sr_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT owner_id FROM service_requests WHERE id = ?", (sr_id,))
    sr = cursor.fetchone()
    if not sr:
        conn.close()
        raise HTTPException(status_code=404, detail="Service request not found")

    cursor.execute("UPDATE service_requests SET status = 'Accepted' WHERE id = ?", (sr_id,))
    cursor.execute("UPDATE service_assignments SET status = 'Accepted' WHERE service_request_id = ?", (sr_id,))
    conn.commit()

    accept_otp = create_and_store_otp(sr_id, "ACCEPT_SERVICE")
    complete_otp = create_and_store_otp(sr_id, "COMPLETE_SERVICE")

    cursor.execute(
        "INSERT INTO notifications (user_id, user_role, title, message, type) VALUES (?, ?, ?, ?, ?)",
        (sr["owner_id"], "owner", "Employee Accepted Job", f"Operator accepted Service #{sr_id}! Accept OTP: {accept_otp}, Complete OTP: {complete_otp}", "service")
    )
    conn.commit()

    formatted = _format_sr_row(conn, sr_id)
    conn.close()
    return formatted

@router.post("/verify-accept-otp", response_model=ServiceRequestResponse)
def verify_accept_otp(payload: VerifyAcceptOtpRequest, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    if not verify_otp_code(payload.service_request_id, payload.otp_code, "ACCEPT_SERVICE"):
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid Accept OTP. Please ask the land owner for the code shown on their screen.")

    cursor.execute("UPDATE service_requests SET status = 'In-Progress' WHERE id = ?", (payload.service_request_id,))
    conn.commit()

    formatted = _format_sr_row(conn, payload.service_request_id)
    conn.close()
    return formatted

@router.post("/verify-complete-otp", response_model=ServiceRequestResponse)
def verify_complete_otp(payload: VerifyCompleteOtpRequest, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    if not verify_otp_code(payload.service_request_id, payload.otp_code, "COMPLETE_SERVICE"):
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid Complete OTP. Please ask the land owner for the completion code.")

    cursor.execute(
        """SELECT sr.*, h.hourly_rate, o.name as owner_name, o.id as owner_id
           FROM service_requests sr
           JOIN harvesters h ON sr.harvester_id = h.id
           JOIN owners o ON sr.owner_id = o.id
           WHERE sr.id = ?""",
        (payload.service_request_id,)
    )
    sr = cursor.fetchone()

    total_hours = payload.total_hours if payload.total_hours > 0 else (sr["land_acres"] * 1.5)
    final_amount = total_hours * sr["hourly_rate"]

    cursor.execute(
        "UPDATE service_requests SET status = 'Completed', total_hours = ?, total_amount = ? WHERE id = ?",
        (total_hours, final_amount, payload.service_request_id)
    )
    conn.commit()

    notify_admin_service_completed(payload.service_request_id, sr["owner_name"], total_hours, final_amount)

    cursor.execute(
        "INSERT INTO notifications (user_id, user_role, title, message, type) VALUES (?, ?, ?, ?, ?)",
        (sr["owner_id"], "owner", "Service Completed", f"Service Job #{payload.service_request_id} finished! Total hours: {total_hours} hrs, Bill: INR {final_amount:.2f}", "billing")
    )
    conn.commit()

    formatted = _format_sr_row(conn, payload.service_request_id)
    conn.close()
    return formatted
