# Defines dependencies used by the routers
from sqlmodel import Session, create_engine
import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session


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
