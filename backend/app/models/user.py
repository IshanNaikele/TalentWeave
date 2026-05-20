import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class UserRole(str, enum.Enum):
    operations_team = "operations_team"
    software_engineer = "software_engineer"
    sales_team = "sales_team"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    level = Column(String, nullable=True)
    dept = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())