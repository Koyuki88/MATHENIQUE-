from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import warnings
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()

# Get the database URL from environment variables, or use SQLite in local dev
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    if ENVIRONMENT == "production":
        warnings.warn(
            "DATABASE_URL is not set in production; falling back to local SQLite which is ephemeral on many hosts.",
            RuntimeWarning,
            stacklevel=2,
        )
    DATABASE_URL = "sqlite:///./mathenique.db"
elif DATABASE_URL.startswith("postgres://"):
    # SQLAlchemy 2.x requires postgresql:// rather than legacy postgres://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs specific connect_args, PostgreSQL does not
connect_args = (
    {"check_same_thread": False, "timeout": 30}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
