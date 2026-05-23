from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Absolute path under Claude's app data — writable when MCP is spawned by Claude Desktop
_db_dir = Path.home() / "Library" / "Application Support" / "Claude"
_db_dir.mkdir(parents=True, exist_ok=True)
_db_path = _db_dir / "chatgpt_task.db"
DATABASE_URL = "sqlite:///" + str(_db_path.resolve())

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
