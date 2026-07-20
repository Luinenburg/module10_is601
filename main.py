# main.py

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator  # Use @validator for Pydantic 1.x
from fastapi.exceptions import RequestValidationError
from app.operations import add, subtract, multiply, divide  # Ensure correct import path
from app.database_init import init_db, drop_db
from app.models.user import User
from app.models.calculation import Calculation
import app.database as database
import uvicorn
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Setup templates directory
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup_event():
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

class SessionResponse(BaseModel):
    token: str = Field(..., description="JWT token")
    user_id: str = Field(..., description="User ID associated with the token")

def SaveCalculation(calculation_data):
    db = database.SessionLocal()
    calculation = Calculation.create(db, calculation_data)
    db.commit()
    return calculation

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
        SaveCalculation({"a": operation.a, "b": operation.b, "calculation_type": "add", "result": result})
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
        SaveCalculation({"a": operation.a, "b": operation.b, "calculation_type": "subtract", "result": result})
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
        SaveCalculation({"a": operation.a, "b": operation.b, "calculation_type": "multiply", "result": result})
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
        SaveCalculation({"a": operation.a, "b": operation.b, "calculation_type": "divide", "result": result})
        return OperationResponse(result=result)
    except ValueError as e:
        logger.error(f"Divide Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Divide Operation Internal Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/users/login", response_model=LoginResponse, responses={401: {"model": ErrorResponse}})
async def login_route(login_data: LoginRequest):
    """
    Authenticate a user and return an authentication token.
    """
    # Use a real DB session and the User.authenticate helper
    db = database.SessionLocal()
    try:
        auth_result = User.authenticate(db, login_data.username, login_data.password)
        if not auth_result:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return LoginResponse(token=auth_result.get("access_token"))
    finally:
        db.close()

@app.post("/users/register", response_model=RegisterResponse, responses={400: {"model": ErrorResponse}})
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
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@app.get("/calculations/{user_id}", response_model=list[OperationResponse], responses={404: {"model": ErrorResponse}})
async def get_user_calculations(user_id: str):
    """
    Retrieve all calculations for a specific user.
    """
    db = database.SessionLocal()
    try:
        calculations = Calculation.get_user_calculation(db, user_id)
        if not calculations:
            raise HTTPException(status_code=404, detail="No calculations found for this user")
        return [OperationResponse(result=calc.result) for calc in calculations]
    finally:
        db.close()

@app.get("/calculations", response_model=list[OperationResponse], responses={404: {"model": ErrorResponse}})
async def get_all_calculations():
    """
    Retrieve all calculations.
    """
    db = database.SessionLocal()
    try:
        calculations = db.query(Calculation).all()
        if not calculations:
            raise HTTPException(status_code=404, detail="No calculations found")
        return [OperationResponse(result=calc.result) for calc in calculations]
    finally:
        db.close()

@app.patch("/calculations/{calculation_id}", response_model=OperationResponse, responses={404: {"model": ErrorResponse}})
async def update_calculation(calculation_id: str, operation: OperationRequest):
    """
    Update a specific calculation by ID.
    """
    db = database.SessionLocal()
    try:
        calculation = Calculation.get_by_id(db, calculation_id)
        if not calculation:
            raise HTTPException(status_code=404, detail="Calculation not found")
        
        # Update the calculation fields
        calculation.a = operation.a
        calculation.b = operation.b
        # Assuming you want to recalculate the result based on the type
        if calculation.calculation_type == "add":
            calculation.result = add(operation.a, operation.b)
        elif calculation.calculation_type == "subtract":
            calculation.result = subtract(operation.a, operation.b)
        elif calculation.calculation_type == "multiply":
            calculation.result = multiply(operation.a, operation.b)
        elif calculation.calculation_type == "divide":
            try:
                calculation.result = divide(operation.a, operation.b)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        db.commit()
        return OperationResponse(result=calculation.result)
    finally:
        db.close()

@app.delete("/calculations/{calculation_id}", response_model=OperationResponse, responses={404: {"model": ErrorResponse}})
async def delete_calculation(calculation_id: str):
    """
    Delete a specific calculation by ID.
    """
    db = database.SessionLocal()
    try:
        calculation = Calculation.get_by_id(db, calculation_id)
        if not calculation:
            raise HTTPException(status_code=404, detail="Calculation not found")
        
        db.delete(calculation)
        db.commit()
        return OperationResponse(result=calculation.result)
    finally:
        db.close()

@app.post("/users/verify-token", response_model=SessionResponse, responses={401: {"model": ErrorResponse}})
async def verify_token_route(token_data: SessionResponse):
    """
    Verify a JWT token and return the associated user ID.
    """
    db = database.SessionLocal()
    try:
        user = User.find_token_in_users(db, token_data.condition)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return SessionResponse(token=token_data.condition, user_id=str(user.id))
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)