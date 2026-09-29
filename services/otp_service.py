import random
import datetime
from database import get_db_connection

def generate_6digit_otp() -> str:
    return str(random.randint(100000, 999999))

def create_and_store_otp(service_request_id: int, purpose: str = "ACCEPT_SERVICE") -> str:
    otp_code = generate_6digit_otp()
    expires_at = (datetime.datetime.now() + datetime.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO otp_verifications (service_request_id, otp_code, purpose, expires_at) VALUES (?, ?, ?, ?)",
        (service_request_id, otp_code, purpose, expires_at)
    )
    conn.commit()
    conn.close()

    print(f"[SMS/OTP SIMULATOR] Generated OTP {otp_code} for Service Request #{service_request_id} ({purpose})")
    return otp_code

def verify_otp_code(service_request_id: int, otp_code: str, purpose: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT id FROM otp_verifications 
           WHERE service_request_id = ? AND otp_code = ? AND purpose = ? AND is_verified = 0 
           ORDER BY id DESC LIMIT 1""",
        (service_request_id, otp_code, purpose)
    )
    row = cursor.fetchone()
    if row:
        otp_id = row["id"]
        cursor.execute("UPDATE otp_verifications SET is_verified = 1 WHERE id = ?", (otp_id,))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False
