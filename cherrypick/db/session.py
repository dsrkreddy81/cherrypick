import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from cherrypick.db.models import Base

load_dotenv()


def get_database_url() -> str:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "cherrypick")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def get_engine():
    return create_engine(get_database_url())


def create_tables(engine):
    Base.metadata.create_all(engine)


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
