from fastapi import APIRouter, HTTPException, Depends
from typing import List
from database import get_db_connection
from models.schemas import FeedbackCreate, FeedbackResponse
from services.auth_service import get_current_user
from services.email_service import notify_admin_feedback_received

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])

@router.get("", response_model=List[FeedbackResponse])
def get_all_feedbacks(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feedback ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("", response_model=FeedbackResponse)
def submit_feedback(payload: FeedbackCreate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM owners WHERE id = ?", (payload.owner_id,))
    owner_row = cursor.fetchone()
    if not owner_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Owner profile not found")

    cursor.execute(
        "INSERT INTO feedback (service_request_id, owner_id, rating, comments, admin_notified) VALUES (?, ?, ?, ?, 1)",
        (payload.service_request_id, payload.owner_id, payload.rating, payload.comments)
    )
    fid = cursor.lastrowid
    conn.commit()

    # Email Admin (vivasaiagencies@gmail.com)
    notify_admin_feedback_received(payload.service_request_id, owner_row["name"], payload.rating, payload.comments or "")

    cursor.execute("SELECT * FROM feedback WHERE id = ?", (fid,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)
