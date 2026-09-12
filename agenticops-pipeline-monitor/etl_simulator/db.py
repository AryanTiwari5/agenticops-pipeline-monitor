import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from models import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# The "engine" is the actual connection pool to Postgres
engine = create_engine(DATABASE_URL)

# SessionLocal is a factory that creates new DB sessions when called
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """
    Creates all tables defined in models.py, if they don't already exist.
    Safe to call every time the app starts — won't wipe existing data.
    """
    Base.metadata.create_all(bind=engine)

def get_session():
    """
    Call this whenever you need to talk to the database.
    Remember to close it when done (or use it in a 'with' block).
    """
    return SessionLocal()