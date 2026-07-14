# main.py

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator  # Use @validator for Pydantic 1.x
from fastapi.exceptions import RequestValidationError
from app.operations import add, subtract, multiply, divide  # Ensure correct import path
from app.database_init import init_db, drop_db
from app.models.user import User
import app.database as database
import uvicorn
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Setup templates directory
templates = Jinja2Templates(directory="templates")

init_db()

# Pydantic model for request data
class OperationRequest(BaseModel):
    a: float = Field(..., description="The first number")
    b: float = Field(..., description="The second number")

    @field_validator('a', 'b')  # Correct decorator for Pydantic 1.x
    def validate_numbers(cls, value):
        if not isinstance(value, (int, float)):
            raise ValueError('Both a and b must be numbers.')
        return value

class LoginRequest(BaseModel):
    username: str = Field(..., description="The username")
    password: str = Field(..., description="The password")

class RegisterRequest(BaseModel):
    username: str = Field(..., description="The username")
    password: str = Field(..., description="The password")
    email: str = Field(..., description="The email")
    fname: str = Field(..., description="The first name")
    lname: str = Field(..., description="The last name")

# Pydantic model for successful response
class OperationResponse(BaseModel):
    result: float = Field(..., description="The result of the operation")

# Pydantic model for error response
class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")

# Response for logins
class LoginResponse(BaseModel):
    token: str = Field(..., description="Authentication token")

# Response for logins
class RegisterResponse(BaseModel):
    message: str = Field(..., description="Registration message")

# Custom Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTPException on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Extracting error messages
    error_messages = "; ".join([f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()])
    logger.error(f"ValidationError on {request.url.path}: {error_messages}")
    return JSONResponse(
        status_code=400,
        content={"error": error_messages},
    )

@app.get("/")
async def read_root(request: Request):
    """
    Serve the index.html template.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/add", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def add_route(operation: OperationRequest):
    """
    Add two numbers.
    """
    try:
        result = add(operation.a, operation.b)
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Add Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/subtract", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def subtract_route(operation: OperationRequest):
    """
    Subtract two numbers.
    """
    try:
        result = subtract(operation.a, operation.b)
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Subtract Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/multiply", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def multiply_route(operation: OperationRequest):
    """
    Multiply two numbers.
    """
    try:
        result = multiply(operation.a, operation.b)
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Multiply Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/divide", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def divide_route(operation: OperationRequest):
    """
    Divide two numbers.
    """
    try:
        result = divide(operation.a, operation.b)
        return OperationResponse(result=result)
    except ValueError as e:
        logger.error(f"Divide Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Divide Operation Internal Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/login", response_model=LoginResponse, responses={401: {"model": ErrorResponse}})
async def login_route(login_data: LoginRequest):
    """
    Authenticate a user and return an authentication token.
    """
    if login_data.username == "admin" and login_data.password == "password":
        token = "fake-jwt-token"
        return LoginResponse(token=token)
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/register", response_model=RegisterResponse, responses={400: {"model": ErrorResponse}})
async def register_route(register_data: RegisterRequest):
    """
    Register a new user.
    """
    # Placeholder for actual registration logic
    new_user = User(
        username=register_data.username,
        password_hash=register_data.password,
        email=register_data.email,
        first_name=register_data.fname,
        last_name=register_data.lname
    )
    # Obtain a real Session instance (get_db() is a generator for FastAPI deps)
    db = database.SessionLocal()
    try:
        new_user.register(db, {
            "first_name": register_data.fname,
            "last_name": register_data.lname,
            "email": register_data.email,
            "username": register_data.username,
            "password": register_data.password
        })
        db.commit()
        return RegisterResponse(message="User registered successfully")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)