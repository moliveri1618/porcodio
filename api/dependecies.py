# Defines dependencies used by the routers
from sqlmodel import Session, create_engine
import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session
from fastapi import HTTPException, Depends
import requests
from fastapi.security import OAuth2PasswordBearer
import logging
import boto3

#Create Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#Load env values in Local & Prod
RUNNING_IN_AWS = os.getenv("AWS_EXECUTION_ENV") is not None
if not RUNNING_IN_AWS:
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    load_dotenv(env_path)
    
DATABASE_URL = os.getenv("DATABASE_URL")


# Connect to db & Initialize tables
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine) # creates the database tables based on the modelds defined using SQLModel

def get_db():
    with Session(engine) as session:
        yield session

# Load Cognito settings from environment variables
COGNITO_REGION = "eu-north-1"
COGNITO_USER_POOL_ID = "eu-north-1_v3F3Ahwnw"
COGNITO_APP_CLIENT_ID = "obemnph8vgsfrcip0s3bg4flm"
COGNITO_PUBLIC_KEY_URL = f"https://cognito-idp.eu-north-1.amazonaws.com/eu-north-1_v3F3Ahwnw/.well-known/jwks.json"
cognito_client = boto3.client("cognito-idp", region_name=COGNITO_REGION)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
def verify_cognito_token(token: str = Depends(oauth2_scheme)):
    """Verify AWS Cognito JWT using Boto3 instead of manual JWT decoding."""
    
    logger.info("Starting token verification using Boto3")
    try:
        response = cognito_client.get_user(AccessToken=token)
        logger.info(f"Token successfully validated. User: {response}")

        return response  

    except Exception as e:
        logger.exception(f"Unexpected error while verifying token: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error during token validation")
