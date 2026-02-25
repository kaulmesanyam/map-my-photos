from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import models
from database import engine, get_db
import auth
import photos_routes

# Create pgvector extension if it doesn't exist, then create tables
# We do this directly via SQL text because pgvector must be enabled before the columns are created
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    conn.commit()

# Create all tables declared in models.py
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Memory Search API", version="1.0.0")

app.include_router(auth.router)
app.include_router(photos_routes.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Memory Search API!"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    # Simple query to test the database connection
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    return {"status": "ok", "database": db_status}

