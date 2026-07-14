from pydantic import BaseModel, EmailStr, Field, ConfigDict, ValidationError, model_validator
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common fields"""
    first_name: str = Field(max_length=50, example="John")
    last_name: str = Field(max_length=50, example="Doe")
    email: EmailStr = Field(example="john.doe@example.com")
    username: str = Field(min_length=3, max_length=50, example="johndoe")

    model_config = ConfigDict(from_attributes=True)


class PasswordMixin(BaseModel):
    """Mixin for password validation"""
    password: str = Field(min_length=6, max_length=128, example="SecurePass123")

    @model_validator(mode="before")
    @classmethod
    def validate_password(cls, values: dict) -> dict:
        password = values.get("password")
        if not password:
            raise ValidationError("Password is required", model=cls) # pragma: no cover
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        if not any(char.isupper() for char in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in password):
            raise ValueError("Password must contain at least one digit")
        return values


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    username: str
    email: str
    first_name: str
    last_name: str
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe123",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "password": "SecurePass123",
            }
        }
    )


class UserLogin(PasswordMixin):
    """Schema for user login"""
    username: str = Field(
        description="Username or email",
        min_length=3,
        max_length=50,
        example="johndoe123"
    )
