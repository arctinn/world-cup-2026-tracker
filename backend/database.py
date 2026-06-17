import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from the .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Create the engine that physically communicates with PostgreSQL
engine = create_engine(DATABASE_URL)

# Create a SessionLocal class. Each instance of this class will be a distinct database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that our future Python database models will inherit from
Base = declarative_base()

# Dependency utility to get a database session for our API routes and close it when done
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()