from fastapi import APIRouter, HTTPException, Depends, status
from database import get_db_connection
from models.schemas import LoginRequest, TokenResponse, UserResponse
from services.auth_service import create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    user = None
    role = None

    # Check Admins
    cursor.execute("SELECT id, email, password_hash, name, phone FROM admins WHERE email = ? OR phone = ?", (payload.email, payload.email))
    admin_row = cursor.fetchone()
    if admin_row:
        user = admin_row
        role = "admin"
    else:
        # Check Owners
        cursor.execute("SELECT id, email, password_hash, name, phone FROM owners WHERE email = ? OR phone = ?", (payload.email, payload.email))
        owner_row = cursor.fetchone()
        if owner_row:
            user = owner_row
            role = "owner"
        else:
            # Check Employees
            cursor.execute("SELECT id, email, password_hash, name, phone FROM employees WHERE email = ? OR phone = ?", (payload.email, payload.email))
            emp_row = cursor.fetchone()
            if emp_row:
                user = emp_row
                role = "employee"

    if not user or user["password_hash"] != payload.password:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please check your email/phone and password."
        )

    token_payload = {
        "user_id": user["id"],
        "email": user["email"],
        "role": role,
        "name": user["name"]
    }
    access_token = create_access_token(token_payload)

    # Save Session in sessions table
    cursor.execute(
        "INSERT INTO sessions (user_id, user_role, token) VALUES (?, ?, ?)",
        (user["id"], role, access_token)
    )
    conn.commit()
    conn.close()

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user["id"],
        name=user["name"],
        email=user["email"],
        role=role
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    role = current_user["role"]
    conn = get_db_connection()
    cursor = conn.cursor()

    if role == "admin":
        cursor.execute("SELECT id, email, phone, name FROM admins WHERE id = ?", (user_id,))
    elif role == "owner":
        cursor.execute("SELECT id, email, phone, name FROM owners WHERE id = ?", (user_id,))
    else:
        cursor.execute("SELECT id, email, phone, name FROM employees WHERE id = ?", (user_id,))

    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")

    return {
        "id": user["id"],
        "email": user["email"],
        "phone": user["phone"],
        "role": role,
        "name": user["name"],
        "status": "active"
    }
