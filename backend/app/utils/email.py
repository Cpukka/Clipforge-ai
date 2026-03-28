import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

async def send_verification_email(email: str):
    # Implementation for sending verification email
    msg = MIMEMultipart()
    msg['From'] = settings.SMTP_USER
    msg['To'] = email
    msg['Subject'] = "Verify Your Email - ClipForge AI"
    
    body = f"Please click the link to verify your email: http://localhost:3000/verify-email?token=..."
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Email sending failed: {e}")