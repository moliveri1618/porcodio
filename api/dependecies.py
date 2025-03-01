# Defines dependencies used by the routers
from sqlmodel import Session, create_engine
import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session


# Create the PostgreSQL database and engine
#rds_postgresql_url = "postgresql://rootuser:diocane1234@database-fastapi-aws.cjo4ss2ailsb.eu-north-1.rds.amazonaws.com:5432/postgres"
#rds_postgresql_url = "postgresql://postgres:password@localhost:5432/PCS_micro"

#Load env values
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)
DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql://rootuser:diocane1234@database-fastapi-aws.cjo4ss2ailsb.eu-north-1.rds.amazonaws.com:5432/postgres"
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
