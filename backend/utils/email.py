# backend/utils/email.py
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")  # Sender email (must be verified in SendGrid)

def send_email(to_email: str, subject: str, body: str):
    # Debug: Print environment variables and inputs
    print(f"SENDGRID_API_KEY: {SENDGRID_API_KEY}")
    print(f"EMAIL_USER: {EMAIL_USER}")
    print(f"Sending email to: {to_email}")
    print(f"Subject: {subject}")
    print(f"Body: {body}")

    # Validate inputs
    if not all([SENDGRID_API_KEY, EMAIL_USER]):
        raise ValueError("Missing SendGrid configuration: Ensure SENDGRID_API_KEY and EMAIL_USER are set in .env")
    if not all([to_email, subject, body]):
        raise ValueError("Missing email parameters: to_email, subject, and body must be provided")

    try:
        message = Mail(
            from_email=EMAIL_USER,
            to_emails=to_email,
            subject=subject,
            plain_text_content=body
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent to {to_email} with status code: {response.status_code}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise