import sqlite3
from config import settings

DB_FILE = settings.DB_NAME

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Admins Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Employees Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            designation TEXT DEFAULT 'Harvester Operator',
            machine_assigned TEXT,
            status TEXT DEFAULT 'available', -- available, busy, off_duty
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Owners Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS owners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            address TEXT,
            land_size_acres REAL DEFAULT 0.0,
            crop_type TEXT DEFAULT 'Paddy',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 4. Harvesters Fleet Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS harvesters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            registration_number TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL, -- Wheel Harvester, Track Harvester, Baler, Transplanter
            hourly_rate REAL NOT NULL,
            status TEXT DEFAULT 'available', -- available, in_use, maintenance
            location TEXT DEFAULT 'Kumbakonam Hub',
            capacity TEXT DEFAULT '5 Acres/Day',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 5. Service Requests Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            harvester_id INTEGER NOT NULL,
            service_date TEXT NOT NULL,
            location TEXT NOT NULL,
            land_acres REAL NOT NULL,
            crop_type TEXT DEFAULT 'Paddy',
            status TEXT DEFAULT 'Waiting', -- Waiting, Assigned, Accepted, In-Progress, Completed, Cancelled
            total_hours REAL DEFAULT 0.0,
            total_amount REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES owners (id),
            FOREIGN KEY (harvester_id) REFERENCES harvesters (id)
        )
    ''')

    # 6. Service Assignments Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_request_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            assigned_by_admin_id INTEGER DEFAULT 1,
            status TEXT DEFAULT 'Assigned', -- Assigned, Accepted, Rejected
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (service_request_id) REFERENCES service_requests (id),
            FOREIGN KEY (employee_id) REFERENCES employees (id),
            FOREIGN KEY (assigned_by_admin_id) REFERENCES admins (id)
        )
    ''')

    # 7. OTP Verifications Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS otp_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_request_id INTEGER NOT NULL,
            otp_code TEXT NOT NULL,
            purpose TEXT NOT NULL, -- ACCEPT_SERVICE, COMPLETE_SERVICE, LOGIN
            is_verified INTEGER DEFAULT 0,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (service_request_id) REFERENCES service_requests (id)
        )
    ''')

    # 8. Feedback Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_request_id INTEGER NOT NULL,
            owner_id INTEGER NOT NULL,
            rating INTEGER NOT NULL, -- 1 to 5
            comments TEXT,
            admin_notified INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (service_request_id) REFERENCES service_requests (id),
            FOREIGN KEY (owner_id) REFERENCES owners (id)
        )
    ''')

    # 9. Notifications Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_role TEXT NOT NULL, -- admin, owner, employee
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            type TEXT DEFAULT 'info',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 10. Sessions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_role TEXT NOT NULL,
            token TEXT NOT NULL,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()

    # Check and Seed Default Data if admins table is empty
    cursor.execute("SELECT COUNT(*) FROM admins")
    if cursor.fetchone()[0] == 0:
        seed_initial_data(cursor)
        conn.commit()

    conn.close()

def seed_initial_data(cursor):
    # 1. Admin
    cursor.execute(
        "INSERT INTO admins (email, password_hash, name, phone) VALUES (?, ?, ?, ?)",
        ("admin@vivasai.com", "admin123", "Vivasai Admin", "7200112053")
    )
    admin_id = cursor.lastrowid

    # 2. Owner
    cursor.execute(
        "INSERT INTO owners (email, phone, password_hash, name, address, land_size_acres, crop_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("owner@vivasai.com", "9876543210", "owner123", "Ramasamy Farmer", "12 Paddy Field St, Karikulam, Kumbakonam", 8.5, "Paddy Rice")
    )
    owner_id = cursor.lastrowid

    # 3. Employee
    cursor.execute(
        "INSERT INTO employees (name, email, phone, password_hash, designation, machine_assigned, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Murugan Operator", "employee@vivasai.com", "9123456789", "emp123", "Senior Fleet Driver", "GAM Harvester 4000", "available")
    )
    employee_id = cursor.lastrowid

    # 4. Fleet Harvesters
    harvesters = [
        ("GAM Harvester 4000", "TN-49-V-1001", "Wheel Harvester", 1800.0, "available", "Kumbakonam Yard", "6 Acres/Day"),
        ("World Star Harvester Pro", "TN-49-V-2002", "Track Harvester", 2200.0, "available", "Myladuthurai Yard", "8 Acres/Day"),
        ("Jaysan Paddy Baler 900", "TN-49-V-3003", "Straw Baler", 1400.0, "available", "Karikulam Depot", "10 Acres/Day"),
        ("Captain Mini Tractor-Harvester", "TN-49-V-4004", "Mini Harvester", 1200.0, "available", "Thanjavur Yard", "4 Acres/Day")
    ]
    for h in harvesters:
        cursor.execute(
            "INSERT INTO harvesters (model_name, registration_number, type, hourly_rate, status, location, capacity) VALUES (?, ?, ?, ?, ?, ?, ?)",
            h
        )

    # 5. Service Request (Waiting -> Assigned)
    cursor.execute(
        """INSERT INTO service_requests 
           (owner_id, harvester_id, service_date, location, land_acres, crop_type, status, total_hours, total_amount) 
           VALUES (?, 1, '2026-10-02', 'Karikulam Paddy Fields', 4.0, 'Paddy', 'Assigned', 0.0, 7200.0)""",
        (owner_id,)
    )
    sr_id = cursor.lastrowid

    # 6. Service Assignment
    cursor.execute(
        "INSERT INTO service_assignments (service_request_id, employee_id, assigned_by_admin_id, status) VALUES (?, ?, ?, 'Assigned')",
        (sr_id, employee_id, admin_id)
    )

    # 7. OTP Verifications (Accept & Complete OTP)
    cursor.execute(
        "INSERT INTO otp_verifications (service_request_id, otp_code, purpose) VALUES (?, '482910', 'ACCEPT_SERVICE')",
        (sr_id,)
    )
    cursor.execute(
        "INSERT INTO otp_verifications (service_request_id, otp_code, purpose) VALUES (?, '739201', 'COMPLETE_SERVICE')",
        (sr_id,)
    )

    # 8. Notifications
    cursor.execute(
        "INSERT INTO notifications (user_id, user_role, title, message, type) VALUES (?, 'owner', ?, ?, 'info')",
        (owner_id, "Welcome to Vivasai Agencies", "Your machinery booking account has been activated. Service Accept OTP is 482910.")
    )

if __name__ == "__main__":
    init_db()
    print("Database re-initialized with 10 tables: admins, employees, owners, harvesters, service_requests, service_assignments, otp_verifications, feedback, notifications, sessions.")
