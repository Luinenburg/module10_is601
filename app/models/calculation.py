# app/models/user.py
from datetime import datetime, timedelta
import uuid
from typing import Optional, Dict, Any

from sqlalchemy import Column, String, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import ValidationError

from app.database import Base
from app.models.user import User  # noqa: F401
from app.schemas.base import UserCreate
from app.schemas.user import UserResponse, Token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Move to config
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Calculation(Base):
    __tablename__ = 'calculations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    a = Column(Float, nullable=False)
    b = Column(Float, nullable=False)
    calculation_type = Column(String(15), nullable=False)
    result = Column(Float, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<Calculation(a={self.a}, b={self.b}, type={self.calculation_type}, result={self.result}, user_id={self.user_id})>"

    @classmethod
    def create(cls, db, calculation_data: Dict[str, Any]) -> "Calculation":
        """Create a new calculation."""
        new_calculation = cls(**calculation_data)
        db.add(new_calculation)
        db.flush()
        return new_calculation
    
    @classmethod
    def get_by_id(cls, db, calculation_id: str) -> Optional["Calculation"]:
        try:
            target_id = uuid.UUID(str(calculation_id))
        except (ValueError, AttributeError):
            return None
        return db.query(cls).filter(cls.id == target_id).first()
    
    @classmethod
    def get_user_calculation(cls, db, user_id: str) -> list["Calculation"]:
        try:
            target_user_id = uuid.UUID(str(user_id))
        except (ValueError, AttributeError):
            return []
        return db.query(cls).filter(cls.user_id == target_user_id).all()