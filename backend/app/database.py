# backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# --- Database URL ---
DATABASE_URL = "postgresql://demo:demo@localhost:5432/demo"

# --- Create the engine ---
engine = create_engine(DATABASE_URL)

# --- Create a Session factory ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Create all tables ---
def init_db():
    Base.metadata.create_all(bind=engine)

# --- Get a database session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()