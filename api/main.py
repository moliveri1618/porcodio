import sys
import os
from fastapi import FastAPI, Depends
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import httpx
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

if os.getenv("GITHUB_ACTIONS"):sys.path.append(os.path.dirname(__file__)) 
from routers import progetti
from routers import clienti
from routers import fornitori
from routers import progetto_fornitore_link
from dependecies import create_db_and_tables, verify_cognito_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(create_db_and_tables)
    yield

app = FastAPI(lifespan=lifespan)
handler = Mangum(app=app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://staging.d1z7mkjg7hq21f.amplifyapp.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], 
    allow_headers=["Content-Type", "Authorization"], 
)

app.include_router(
    progetti.router, 
    prefix="/progetti", 
    tags=["progetti"]
)

app.include_router(
    clienti.router, 
    prefix="/clienti", 
    tags=["clienti"]
)

app.include_router(
    fornitori.router, 
    prefix="/fornitori", 
    tags=["fornitori"]
)

app.include_router(
    progetto_fornitore_link.router, 
    prefix="/progetti-fornitori", 
    tags=["progetti-fornitori"]
)


@app.get("/")
async def root(current_user: dict = Depends(verify_cognito_token)):
    
    return {"message": "Hello"}


API_BASE = "https://www.tigulliocrm.it/api"
API_URL = "https://www.tigulliocrm.it/api/fornitori/"
API_KEY = "xAe5xrokrKL4g7sbyGHQ3mZ9wyqUVks7"

@app.get("/")
def root():
    return {"message": "FastAPI test client is running"}

@app.get("/test-fornitori")
def test_fornitori():
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    try:
        response = httpx.get(API_URL, headers=headers, timeout=30.0)
        return {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/test-dip-tecnico")
def test_dip_tecnico():
    """Calls the dip-tecnico API with Bearer token in header"""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        response = httpx.get(f"{API_BASE}/dip-tecnico/", headers=headers, timeout=30.0)
        return {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text
        }
    except Exception as e:
        return {"error": str(e)}
    
    
@app.get("/send-email")
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