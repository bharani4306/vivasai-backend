from fastapi import APIRouter, Depends
from typing import List
from database import get_db_connection
from models.schemas import NotificationResponse
from services.auth_service import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationResponse])
def get_user_notifications(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if current_user["role"] == "admin":
        cursor.execute("SELECT * FROM notifications WHERE user_role = 'admin' ORDER BY id DESC")
    else:
        cursor.execute(
            "SELECT * FROM notifications WHERE user_id = ? AND user_role = ? ORDER BY id DESC",
            (current_user["user_id"], current_user["role"])
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.put("/{notification_id}/read")
def mark_notification_read(notification_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
    conn.commit()
    conn.close()
    return {"message": "Notification marked as read"}
