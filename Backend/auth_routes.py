"""
Authentication routes for login and signup
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
import os
from urllib.parse import urlencode

# Check if database is available
try:
    from database import database
    from db_operations import get_user_by_email, create_user_with_password, get_user_by_username, create_user
    from auth import hash_password, verify_password, create_access_token
    DB_AVAILABLE = database is not None
except ImportError:
    DB_AVAILABLE = False
    database = None

# Google OAuth imports
try:
    import httpx
    GOOGLE_OAUTH_AVAILABLE = True
except ImportError:
    GOOGLE_OAUTH_AVAILABLE = False
    print("Warning: httpx not available. Google OAuth will be disabled.")

def is_database_connected():
    """Check if database is actually connected"""
    print(f"DEBUG: Checking DB connection. DB_AVAILABLE={DB_AVAILABLE}, database={database}")
    if not DB_AVAILABLE or database is None:
        return False
    try:
        # Check connection status from database module
        from database import DATABASE_CONNECTED
        print(f"DEBUG: DATABASE_CONNECTED from module={DATABASE_CONNECTED}")
        if DATABASE_CONNECTED:
            return True
            
        # Fallback: Check if database has a connection pool
        print(f"DEBUG: Checking fallback pool")
        if hasattr(database, '_database'):
            pool = getattr(database._database, '_pool', None)
            print(f"DEBUG: Pool found: {pool is not None}")
            if pool is not None:
                return True
        else:
            print("DEBUG: database object has no _database attr")
    except Exception as e:
        print(f"DEBUG: Error in is_database_connected: {e}")
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
    voice_id: Optional[str] = None
    voice_name: Optional[str] = None


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
        print(f"DEBUG: Exception in signup: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=503,
            detail=f"Database connection error: {e}"
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
        name=user.get("name"),
        voice_id=user.get("voice_id"),
        voice_name=user.get("voice_name")
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
        print(f"DEBUG: Exception in signup: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=503,
            detail=f"Database connection error: {e}"
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
            name=new_user.get("name"),
            voice_id=new_user.get("voice_id"),
            voice_name=new_user.get("voice_name")
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except (AssertionError, AttributeError) as e:
        print(f"DEBUG: Exception in signup: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=503,
            detail=f"Database connection error: {e}"
        )
    except Exception as e:
        error_msg = str(e).lower()
        if "unique constraint" in error_msg or "already exists" in error_msg:
            raise HTTPException(status_code=400, detail="An account with this email already exists. Please sign in instead.")
        elif "password cannot be longer than 72 bytes" in error_msg or "72 bytes" in error_msg:
            raise HTTPException(status_code=400, detail="Password is too long. Please use a password with 72 bytes or fewer (approximately 72 ASCII characters).")
        raise HTTPException(status_code=400, detail=f"Error creating account: {str(e)}")


# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
GOOGLE_REDIRECT_URI = f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/api/auth/google/callback"

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


class GoogleAuthResponse(BaseModel):
    auth_url: str


@router.get("/google", response_model=GoogleAuthResponse)
async def google_auth_initiate():
    """
    Initiate Google OAuth flow - returns the authorization URL
    """
    if not GOOGLE_OAUTH_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not available. Please install required dependencies."
        )
    
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Please set GOOGLE_CLIENT_ID in environment variables."
        )
    
    # Build authorization URL
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account"
    }
    
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    
    return GoogleAuthResponse(auth_url=auth_url)


@router.get("/google/callback")
async def google_auth_callback(code: str = Query(...)):
    """
    Handle Google OAuth callback - exchange code for token and create/login user
    """
    if not GOOGLE_OAUTH_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not available."
        )
    
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured."
        )
    
    if not is_database_connected():
        raise HTTPException(
            status_code=503,
            detail="Database is not available."
        )
    
    try:
        # Exchange authorization code for access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code"
                }
            )
            
            if token_response.status_code != 200:
                error_detail = token_response.text
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to exchange code for token: {error_detail}"
                )
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                raise HTTPException(
                    status_code=400,
                    detail="No access token received from Google"
                )
            
            # Get user info from Google
            user_info_response = await client.get(
                GOOGLE_USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_info_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to get user info from Google"
                )
            
            user_info = user_info_response.json()
            google_email = user_info.get("email", "").lower().strip()
            google_name = user_info.get("name")
            google_id = user_info.get("id")
            
            if not google_email:
                raise HTTPException(
                    status_code=400,
                    detail="No email provided by Google"
                )
            
            # Check if user already exists
            existing_user = await get_user_by_email(google_email)
            
            if existing_user:
                # User exists - log them in
                user = existing_user
            else:
                # Create new user (no password for OAuth users)
                new_user = await create_user(
                    email=google_email,
                    name=google_name
                )
                user = new_user
            
            # Create JWT token
            access_token_jwt = create_access_token(
                data={"sub": str(user["id"]), "email": user["email"]}
            )
            
            # Redirect to frontend with token in URL (frontend will extract it)
            redirect_url = f"{FRONTEND_URL}/auth/callback?token={access_token_jwt}&user_id={user['id']}&email={user['email']}"
            if user.get("name"):
                redirect_url += f"&name={user['name']}"
            
            return RedirectResponse(url=redirect_url)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Google OAuth error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error during Google authentication: {str(e)}"
        )

