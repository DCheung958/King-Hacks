"""
Authentication routes for login and signup
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

# Check if database is available
try:
    from database import database
    from db_operations import get_user_by_email, create_user_with_password, get_user_by_username
    from auth import hash_password, verify_password, create_access_token
    DB_AVAILABLE = database is not None
except ImportError:
    DB_AVAILABLE = False
    database = None

def is_database_connected():
    """Check if database is actually connected"""
    if not DB_AVAILABLE or database is None:
        return False
    try:
        # Check connection status from database module
        from database import DATABASE_CONNECTED
        return DATABASE_CONNECTED
    except (AttributeError, ImportError):
        # Fallback: Check if database has a connection pool
        try:
            if hasattr(database, '_database'):
                pool = getattr(database._database, '_pool', None)
                if pool is not None:
                    return True
        except (AttributeError, AssertionError):
            pass
        return False

router = APIRouter(prefix="/api/auth", tags=["authentication"])


# Request/Response Models
class LoginRequest(BaseModel):
    email: str  # Can be email or username
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    name: Optional[str] = None


@router.post("/login", response_model=AuthResponse)
async def login(credentials: LoginRequest):
    """
    Login endpoint - only logs in existing users
    """
    if not is_database_connected():
        raise HTTPException(
            status_code=503,
            detail="Database is not available. Please set up the database first. Check your PostgreSQL connection and credentials."
        )
    
    email = credentials.email.strip().lower()
    password = credentials.password
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    
    # Check if user exists (try email first, then username)
    try:
        user = await get_user_by_email(email)
        if not user:
            # Try username
            user = await get_user_by_username(email)
    except (AssertionError, AttributeError) as e:
        raise HTTPException(
            status_code=503,
            detail="Database connection error. Please ensure PostgreSQL is running and credentials are correct."
        )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please create an account first.")
    
    # User exists - verify password
    if not user.get("password_hash"):
        raise HTTPException(
            status_code=400,
            detail="Account exists but has no password. Please contact support."
        )
    
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    # Password correct - create token
    access_token = create_access_token(data={"sub": str(user["id"]), "email": user["email"]})
    
    return AuthResponse(
        access_token=access_token,
        user_id=str(user["id"]),
        email=user["email"],
        name=user.get("name")
    )


class SignupRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


@router.post("/signup", response_model=AuthResponse)
async def signup(credentials: SignupRequest):
    """
    Signup endpoint - only creates new accounts
    """
    if not is_database_connected():
        raise HTTPException(
            status_code=503,
            detail="Database is not available. Please set up the database first. Check your PostgreSQL connection and credentials."
        )
    
    email = credentials.email.strip().lower()
    password = credentials.password
    name = credentials.name.strip() if credentials.name else None
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    
    # Validate password length (bcrypt has 72 byte limit)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password is too long. Please use a password with 72 bytes or fewer (approximately 72 ASCII characters)."
        )
    
    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters long."
        )
    
    # Validate email format
    if "@" not in email:
        raise HTTPException(
            status_code=400,
            detail="Please use a valid email address"
        )
    
    # Check if user already exists
    try:
        existing_user = await get_user_by_email(email)
        if existing_user:
            raise HTTPException(status_code=400, detail="An account with this email already exists. Please sign in instead.")
    except (AssertionError, AttributeError) as e:
        raise HTTPException(
            status_code=503,
            detail="Database connection error. Please ensure PostgreSQL is running and credentials are correct."
        )
    
    # Create user with password
    try:
        password_hash = hash_password(password)
        new_user = await create_user_with_password(
            email=email,
            password_hash=password_hash,
            name=name
        )
        
        # Create token for new user
        access_token = create_access_token(data={"sub": new_user["id"], "email": new_user["email"]})
        
        return AuthResponse(
            access_token=access_token,
            user_id=new_user["id"],
            email=new_user["email"],
            name=new_user.get("name")
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except (AssertionError, AttributeError) as e:
        raise HTTPException(
            status_code=503,
            detail="Database connection error. Please ensure PostgreSQL is running and credentials are correct."
        )
    except Exception as e:
        error_msg = str(e).lower()
        if "unique constraint" in error_msg or "already exists" in error_msg:
            raise HTTPException(status_code=400, detail="An account with this email already exists. Please sign in instead.")
        elif "password cannot be longer than 72 bytes" in error_msg or "72 bytes" in error_msg:
            raise HTTPException(status_code=400, detail="Password is too long. Please use a password with 72 bytes or fewer (approximately 72 ASCII characters).")
        raise HTTPException(status_code=400, detail=f"Error creating account: {str(e)}")

