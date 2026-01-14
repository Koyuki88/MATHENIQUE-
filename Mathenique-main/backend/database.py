from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import os.path
from dotenv import load_dotenv

load_dotenv()

# Get the database URL from environment variables, or use SQLite as a fallback
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mathenique.db")

# SQLite needs specific connect_args, PostgreSQL does not
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(
    DATABASE_URL, connect_args=connect_args
)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

Base = declarative_base()
