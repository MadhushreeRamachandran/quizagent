# Database/database.py
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
 
from config.config import *
 
class Database:
    def __init__(self):
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(
            bind=self.engine,  
            autoflush=False,
            autocommit=False,
            future=True,
        )
 
    def _create_engine(self):
        db_url = (
            f"postgresql+psycopg2://{DB_USER}:"
            f"{DB_PASSWORD}@"
            f"{DB_HOST}:{DB_PORT}/"
            f"{DB_NAME}"
        )
        return create_engine(db_url, pool_pre_ping=True, future=True)
 
    def get_session(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
 
    def inspector(self):
        return inspect(self.engine)
 
    def test_connection(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
 

db_provider = Database()
 