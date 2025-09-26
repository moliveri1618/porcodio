import io
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
from fastapi.responses import StreamingResponse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# if os.getenv("GITHUB_ACTIONS"): sys.path.append(os.path.dirname(__file__)) 
# from models.fornitori import Fornitore  # Changed model name from Cliente to Fornitori
# from schemas.fornitori import FornitoriCreate, FornitoriRead, FornitoriUpdate  # Updated schemas
# from dependecies import get_db

router = APIRouter()


@router.get("/send-email")
def send_email_to_user():
    sender_email = "lastiada1@gmail.com"
    receiver_email = "mauro.oliveri16@gmail.com"
    password = "opqexobtkprukiyi"   # Use environment variable in production!

    subject = "Test Email"
    body = "Hello, this is a test email sent from Python!"

    try:
        # Create email message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Connect to SMTP and send
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(message)

        return {"status_code": 200, "result": f"Email sent to {receiver_email}"}


    except smtplib.SMTPAuthenticationError:
        return {"status_code": 401, "error": "Authentication failed. Check SMTP_USER/SMTP_PASS (app password)."}
    except smtplib.SMTPConnectError as e:
        # Connection-level SMTP failure
        err = getattr(e, "smtp_error", b"")
        err = err.decode(errors="ignore") if isinstance(err, bytes) else str(err or e)
        return {"status_code": 503, "error": f"SMTP connect error: {err}"}
    except smtplib.SMTPResponseException as e:
        # Generic 4xx/5xx SMTP response
        code = getattr(e, "smtp_code", 500)
        err = getattr(e, "smtp_error", b"")
        err = err.decode(errors="ignore") if isinstance(err, bytes) else str(err or e)
        return {"status_code": code, "error": err}
    except Exception as e:
        return {"status_code": 500, "error": str(e)}