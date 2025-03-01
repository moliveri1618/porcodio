# Defines dependencies used by the routers
from sqlmodel import Session, create_engine
import os
from sqlmodel import SQLModel, Field, create_engine, Session, select

# Create the PostgreSQL database and engine
rds_postgresql_url = "postgresql://rootuser:diocane1234@database-fastapi-aws.cjo4ss2ailsb.eu-north-1.rds.amazonaws.com:5432/postgres"
#rds_postgresql_url = "postgresql://postgres:password@localhost:5432/PCS_micro"

# Create the database engine
engine = create_engine(rds_postgresql_url, echo=True)

# Initialize the database
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Dependency for database session management
def get_db():
    with Session(engine) as session:
        yield session
