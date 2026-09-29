import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings

def send_email_notification(to_email: str, subject: str, body: str):
    try:
        print(f"\n======== [EMAIL NOTIFICATION DISPATCH] ========")
        print(f"TO: {to_email}")
        print(f"SUBJECT: {subject.encode('ascii', 'ignore').decode()}")
        print(f"BODY:\n{body.encode('ascii', 'ignore').decode()}")
        print(f"===============================================\n")
    except Exception:
        pass

    # In production, SMTP connection sends the actual email:
    try:
        if settings.SMTP_USER != "vivasaiagencies@gmail.com" or settings.SMTP_PASSWORD != "mock_app_password":
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_USER
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
    except Exception as e:
        print(f"[EMAIL SERVICE WARNING] SMTP Send skipped/deferred: {str(e)}")

def notify_admin_new_service_request(sr_id: int, owner_name: str, land_acres: float, harvester_name: str):
    subject = f"[Vivasai Agencies] New Service Booking #{sr_id} - {owner_name}"
    body = (
        f"Hello Vivasai Agencies Admin,\n\n"
        f"A new harvester service request #{sr_id} has been submitted by owner: {owner_name}.\n"
        f"Details:\n"
        f"- Land Size: {land_acres} Acres\n"
        f"- Harvester Requested: {harvester_name}\n"
        f"- Email Admin Contact: {settings.ADMIN_EMAIL}\n\n"
        f"Please assign an available employee/operator from the Admin Dashboard.\n\n"
        f"Regards,\n"
        f"Vivasai Agencies Automated System"
    )
    send_email_notification(settings.ADMIN_EMAIL, subject, body)

def notify_admin_service_completed(sr_id: int, owner_name: str, total_hours: float, total_amount: float):
    subject = f"[Vivasai Agencies] Service Completed #{sr_id} - Billing INR {total_amount:.2f}"
    body = (
        f"Hello Vivasai Agencies Admin,\n\n"
        f"Service Request #{sr_id} for {owner_name} has been successfully verified with OTP & completed.\n"
        f"Summary:\n"
        f"- Total Operating Hours: {total_hours} Hours\n"
        f"- Total Amount Charged: INR {total_amount:.2f}\n\n"
        f"The invoice has been generated.\n\n"
        f"Regards,\n"
        f"Vivasai Agencies Fleet System"
    )
    send_email_notification(settings.ADMIN_EMAIL, subject, body)

def notify_admin_feedback_received(sr_id: int, owner_name: str, rating: int, comments: str):
    subject = f"[Vivasai Agencies] New Feedback Received - {rating} Stars"
    body = (
        f"Hello Admin,\n\n"
        f"Owner {owner_name} submitted feedback for Service #{sr_id}:\n"
        f"- Rating: {rating}/5 Stars\n"
        f"- Comments: {comments or 'No written comments.'}\n\n"
        f"Regards,\n"
        f"Vivasai Agencies Service Care"
    )
    send_email_notification(settings.ADMIN_EMAIL, subject, body)
