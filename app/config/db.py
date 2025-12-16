import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

root_path = Path(__file__).parent.parent.parent
env_path = root_path / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME")
DB_SCHEMA = os.getenv("DB_SCHEMA")

missing_vars = [
    name
    for name, value in [
        ("DB_USERNAME", DB_USERNAME),
        ("DB_PASSWORD", DB_PASSWORD),
        ("DB_HOST", DB_HOST),
        ("DB_NAME", DB_NAME),
    ]
    if not value
]

if missing_vars:
    raise RuntimeError(f"Missing required database environment variables: {', '.join(missing_vars)}")

base_url = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
if DB_SCHEMA:
    DATABASE_URL = base_url + f"?options=-c%20search_path%3D{DB_SCHEMA}"
else:
    DATABASE_URL = base_url

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_size=10,  # Keep 10 persistent connections
    max_overflow=20,  # Allow 20 more connections on demand
    pool_pre_ping=True,  # Check connection health before using
    pool_recycle=300,  # Recycle connections every 5 minutes
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
