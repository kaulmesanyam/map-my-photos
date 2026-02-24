import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

# We default to the docker-compose credentials if no .env is found
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://myuser:mypassword@localhost:5432/photos_db"
)

# Initialize the SQLAlchemy Engine
engine = create_engine(DATABASE_URL)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our models
Base = declarative_base()

# Dependency to get DB session in FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
