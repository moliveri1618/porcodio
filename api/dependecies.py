# Defines dependencies used by the routers
from sqlmodel import Session, create_engine
import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session
from fastapi import HTTPException, Depends
import requests
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.api_jwk import PyJWK
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Load Cognito settings from environment variables
COGNITO_REGION = os.getenv("COGNITO_REGION", "eu-north-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "eu-north-1_v3F3Ahwnw")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID", "obemnph8vgsfrcip0s3bg4flm")
COGNITO_PUBLIC_KEY_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_cognito_public_keys():
    response = requests.get(COGNITO_PUBLIC_KEY_URL)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch Cognito public keys")
    return response.json()

# ✅ Function to verify JWT token
def verify_cognito_token(token: str = Depends(oauth2_scheme)):
    logger.info("Starting token verification")
    
    try:
        logger.info("Decoding JWT header")
        # Decode JWT header to get key ID (kid)
        headers = jwt.get_unverified_header(token)
        kid = headers["kid"]
        logger.info(f"Extracted kid: {kid}")


        # Fetch Cognito public keys
        jwks = get_cognito_public_keys()
        logger.info(f"JWKS Keys: {jwks}")

        # Find the correct key
        key = next((key for key in jwks["keys"] if key["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Invalid token: Key not found")

        # Construct the public key using PyJWK
        # Use PyJWK.from_dict for a dictionary instead of from_json
        public_key = PyJWK.from_dict(key).key

        # Decode and verify the token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,  # Validate token is for your app
            issuer=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
        )

        return payload  # Returns the user info from the token

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    
#Load env values
RUNNING_IN_AWS = os.getenv("AWS_EXECUTION_ENV") is not None

if not RUNNING_IN_AWS:
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    load_dotenv(env_path)
    
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing in .env file!")

# Create the database engine
engine = create_engine(DATABASE_URL, echo=True)

# Initialize the database
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Dependency for database session management
def get_db():
    with Session(engine) as session:
        yield session
