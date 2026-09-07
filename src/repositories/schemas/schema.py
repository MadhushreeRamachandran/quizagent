from sqlalchemy import (
    Column, Integer,  DateTime, String, Boolean,  text
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ErrorLog(Base):
    __tablename__="errors"
    error_id=Column(Integer,primary_key=True,autoincrement=True)
    file_name=Column(String(255),nullable= False)
    function_name=Column(String(255),nullable= False)
    error_message=Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    created_by = Column(String, default="SYSTEM", nullable=False)
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_by = Column(String, default="SYSTEM", nullable=False)
