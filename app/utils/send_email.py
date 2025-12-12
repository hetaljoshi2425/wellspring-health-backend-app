import aiosmtplib
from email.message import EmailMessage
from email.mime.image import MIMEImage
import os

from dotenv import load_dotenv
load_dotenv()

# SMTP Send Email Creds
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL")


async def send_reset_email(to_email: str, reset_link: str):
    """Send a password reset email with embedded inline logo."""
    
    # Load HTML template
    template_path = "app/templates/reset_password_email.html"
    with open(template_path, "r") as file:
        html_content = file.read()

    # Replace placeholders in HTML
    html_content = html_content.replace("{{RESET_LINK}}", reset_link)

    # Create email
    message = EmailMessage()
    message["From"] = "Wellspring Support {FROM_EMAIL}"
    message["To"] = to_email
    message["Subject"] = "Reset Your Password"
    message.set_content("HTML email not supported.")
    message.add_alternative(html_content, subtype="html")
    
    logo_file = "app/static/logo.png"
    # Attach the logo image inline
    # with open(logo_file, 'rb') as f:
    #     logo_file = MIMEImage(f.read())
    #     logo_file.add_header('Content-ID', '<logo>')
    #     message.attach(logo_file)


    # Send email via SMTP
    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            start_tls=True,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
        )
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print("Email sending failed:", e)
        return False
    