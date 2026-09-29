# Vivasai Agencies - Backend API

FastAPI backend application for Vivasai Agencies Agricultural Harvester Fleet & Service Management System.

## Features
- **10 SQLite Tables**: Users, Owners, Employees, Harvesters, Service Requests, OTPs, Feedbacks, Notifications, Addresses, System Settings.
- **JWT Authentication**: Secured Bearer Token authorization for Admin, Owner, and Employee roles.
- **OTP Workflow**:
  - Service Accept OTP & Completion OTP generated for Land Owners.
  - Displayed on Owner Dashboard / Service Details screen.
  - Verified by Employee app before starting or finishing field service.
- **Email Notifications**: Automatic notification dispatched to `vivasaiagencies@gmail.com` on new service request, completed billing, and feedback submission.

## Setup & Running

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run Backend Server**:
```bash
python main.py
```
Or with uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. **Interactive Swagger API Documentation**:
Open browser at `http://localhost:8000/docs`

## Seed Credentials
- **Admin**: `admin@vivasai.com` / `admin123`
- **Owner**: `owner@vivasai.com` / `owner123`
- **Employee**: `employee@vivasai.com` / `emp123`
