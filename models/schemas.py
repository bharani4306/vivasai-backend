from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# --- Auth & User Schemas ---
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    email: str
    role: str

class UserResponse(BaseModel):
    id: int
    email: str
    phone: str
    role: str
    name: str
    status: str

# --- Owner Schemas ---
class OwnerCreate(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    address: str
    land_size_acres: float = 0.0
    crop_type: str = "Paddy"

class OwnerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    land_size_acres: Optional[float] = None
    crop_type: Optional[str] = None

class OwnerResponse(BaseModel):
    id: int
    user_id: int
    name: str
    phone: str
    address: Optional[str] = None
    land_size_acres: float
    crop_type: str
    created_at: str

# --- Employee Schemas ---
class EmployeeCreate(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    designation: str = "Harvester Operator"
    machine_assigned: Optional[str] = "GAM Harvester 4000"

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    machine_assigned: Optional[str] = None
    status: Optional[str] = None

class EmployeeResponse(BaseModel):
    id: int
    user_id: int
    name: str
    phone: str
    designation: str
    machine_assigned: Optional[str] = None
    status: str
    created_at: str

# --- Harvester Schemas ---
class HarvesterCreate(BaseModel):
    model_name: str
    registration_number: str
    type: str
    hourly_rate: float
    location: str = "Kumbakonam Hub"
    capacity: str = "5 Acres/Day"

class HarvesterUpdate(BaseModel):
    model_name: Optional[str] = None
    registration_number: Optional[str] = None
    type: Optional[str] = None
    hourly_rate: Optional[float] = None
    status: Optional[str] = None
    location: Optional[str] = None
    capacity: Optional[str] = None

class HarvesterResponse(BaseModel):
    id: int
    model_name: str
    registration_number: str
    type: str
    hourly_rate: float
    status: str
    location: str
    capacity: str

# --- Service Request Schemas ---
class ServiceRequestCreate(BaseModel):
    owner_id: int
    harvester_id: int
    service_date: str
    location: str
    land_acres: float
    crop_type: str = "Paddy"

class VerifyAcceptOtpRequest(BaseModel):
    service_request_id: int
    otp_code: str
    employee_id: int

class VerifyCompleteOtpRequest(BaseModel):
    service_request_id: int
    otp_code: str
    total_hours: float

class ServiceRequestResponse(BaseModel):
    id: int
    owner_id: int
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    employee_id: Optional[int] = None
    employee_name: Optional[str] = None
    harvester_id: int
    harvester_name: Optional[str] = None
    service_date: str
    location: str
    land_acres: float
    crop_type: str
    status: str
    service_accept_otp: Optional[str] = None
    service_complete_otp: Optional[str] = None
    total_hours: float
    total_amount: float
    created_at: str

# --- OTP Schemas ---
class OtpGenerateRequest(BaseModel):
    phone_or_email: str
    purpose: str = "ACCEPT_SERVICE"

class OtpVerifyRequest(BaseModel):
    phone_or_email: str
    otp_code: str
    purpose: str

# --- Feedback Schemas ---
class FeedbackCreate(BaseModel):
    service_request_id: int
    owner_id: int
    rating: int  # 1 to 5
    comments: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    service_request_id: int
    owner_id: int
    rating: int
    comments: Optional[str] = None
    admin_notified: int
    created_at: str

# --- Notification Schemas ---
class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    is_read: int
    type: str
    created_at: str

# --- Address Schemas ---
class AddressCreate(BaseModel):
    owner_id: int
    address_line: str
    village: str
    district: str = "Kumbakonam"
    pincode: str
    is_primary: bool = True

class AddressResponse(BaseModel):
    id: int
    owner_id: int
    address_line: str
    village: str
    district: str
    pincode: str
    is_primary: int
