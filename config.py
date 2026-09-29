import os

class Settings:
    APP_NAME: str = "Vivasai Agencies Harvester Management"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "vivasai_agencies_super_secret_jwt_key_2026_kumbakonam")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 Hours
    
    DB_NAME: str = os.getenv("DB_NAME", "vivasai_agencies.db")
    
    # Email / Contact Settings
    ADMIN_EMAIL: str = "vivasaiagencies@gmail.com"
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "vivasaiagencies@gmail.com")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "mock_app_password")
    
    COMPANY_PHONE: str = "7200112053"
    COMPANY_SECONDARY_PHONE: str = "9445337018"
    COMPANY_ADDRESS: str = "18, Sabari Nagar, Myladuthurai Main Road, Karikulam, Kumbakonam"

settings = Settings()
