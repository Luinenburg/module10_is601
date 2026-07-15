from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

class CalculationCreate(BaseModel):
    a: float
    b: float
    calculation_type: str
    result: float
    user_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)

class CalculationRead(BaseModel):
    id: UUID
    a: float
    b: float
    calculation_type: str
    result: float
    user_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)