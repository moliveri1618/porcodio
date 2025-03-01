# Defines dependencies used by the routers
from sqlmodel import Session, create_engine
import os
from sqlmodel import SQLModel, Field, create_engine, Session, select

# Define the database connection URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/PCS_micro")

# Create the database engine
engine = create_engine(DATABASE_URL, echo=True)

# Initialize the database
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Dependency for database session management
def get_db():
    with Session(engine) as session:
        yield session
