from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from config import settings

from routers import (
    auth_router,
    owner_router,
    employee_router,
    harvester_router,
    service_request_router,
    feedback_router,
    notification_router
)

app = FastAPI(
    title=settings.APP_NAME,
    description="Vivasai Agencies Harvester Fleet Management & Service OTP System",
    version="1.0.0"
)

# Enable CORS for Flutter mobile/web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "company": "Vivasai Agencies",
        "location": settings.COMPANY_ADDRESS,
        "phones": [settings.COMPANY_PHONE, settings.COMPANY_SECONDARY_PHONE],
        "email_admin": settings.ADMIN_EMAIL,
        "status": "Online",
        "documentation": "/docs"
    }

# Include all 7 Routers
app.include_router(auth_router.router)
app.include_router(owner_router.router)
app.include_router(employee_router.router)
app.include_router(harvester_router.router)
app.include_router(service_request_router.router)
app.include_router(feedback_router.router)
app.include_router(notification_router.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
