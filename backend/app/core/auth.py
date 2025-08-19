from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel
from starlette import status
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

# Add the parent directory to sys.path for local development
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
    print(f"Added {parent_dir} to sys.path from auth.py")

# Fix imports for different environments
try:
    # Try relative imports first
    from ..db.database import SessionLocal
    from ..models.models import User
    from .google_oauth import google_oauth_service
    print("Auth: Using relative imports")
except ImportError:
    try:
        # Try absolute imports with backend prefix
        from backend.app.db.database import SessionLocal
        from backend.app.models.models import User
        from backend.app.core.google_oauth import google_oauth_service
        print("Auth: Using backend.app.* imports")
    except ImportError:
        # Fallback to local imports
        from app.db.database import SessionLocal
        from app.models.models import User
        from app.core.google_oauth import google_oauth_service
        print("Auth: Using app.* imports")

from passlib.context import CryptContext

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)

# Use environment variable with fallback to default value
SECRET_KEY = os.environ.get("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="api/auth/token")

class CreateUserRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    username: str
    id: int
    email: str = None
    auth_method: str = "local"

class GoogleAuthRequest(BaseModel):
    code: str
    state: str
    nonce: Optional[str] = None

# In-memory storage for OAuth state (use Redis in production)
oauth_states = {}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(create_user_request: CreateUserRequest, db: db_dependency):
    
    create_user_model = User(
        username=create_user_request.username,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        auth_method="local"
    )

    db.add(create_user_model)
    db.commit()

    return {"message": "User created successfully"}

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    
    user = authenticate_user(form_data.username, form_data.password, db)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    
    token = create_access_token(username=user.username, user_id=user.id, expires_delta=timedelta(minutes=20))
    return {"access_token": token, "token_type": "bearer"}

def authenticate_user(username: str, password: str, db: db_dependency):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id}
    expires = datetime.utcnow() + expires_delta
    encode.update({"exp": expires})
    access_token = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
    return access_token

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                                detail="Could not validate credentials")
        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

@router.get("/users/me", response_model=UserResponse)
async def get_user(current_user: Annotated[dict, Depends(get_current_user)], db: db_dependency):
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return {
        "username": user.username,
        "id": user.id,
        "email": user.email,
        "auth_method": user.auth_method
    }

# Google OAuth endpoints
@router.get("/google/authorize")
async def google_authorize():
    """Get Google OAuth authorization URL with security parameters"""
    try:
        auth_data = google_oauth_service.get_authorization_url()
        
        # Store state and nonce for validation (use Redis in production)
        oauth_states[auth_data["state"]] = {
            "nonce": auth_data["nonce"],
            "created_at": datetime.utcnow()
        }
        
        return {
            "authorization_url": auth_data["authorization_url"],
            "state": auth_data["state"]
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/google/callback", response_model=Token)
async def google_callback(google_auth: GoogleAuthRequest, db: db_dependency):
    """Handle Google OAuth callback and create/authenticate user with security validation"""
    try:
        print(f"Received Google callback data: code={google_auth.code[:10]}..., state={google_auth.state}, nonce={google_auth.nonce}")
        print(f"Available oauth_states: {list(oauth_states.keys())}")
        
        # Validate state parameter
        if google_auth.state not in oauth_states:
            print(f"State validation failed. Expected one of: {list(oauth_states.keys())}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state parameter"
            )
        
        stored_data = oauth_states[google_auth.state]
        nonce = stored_data["nonce"]
        print(f"Retrieved stored nonce: {nonce}")
        
        # Clean up stored state
        del oauth_states[google_auth.state]
        print("Cleaned up stored state")
        
        # Exchange code for tokens with state validation
        print("Exchanging code for tokens...")
        tokens = await google_oauth_service.exchange_code_for_tokens(
            google_auth.code, 
            google_auth.state, 
            google_auth.state
        )
        print(f"Token exchange successful: {list(tokens.keys())}")
        
        # Verify ID token if present
        if "id_token" in tokens:
            print("Verifying ID token...")
            id_token_data = await google_oauth_service.verify_id_token(tokens["id_token"], nonce)
            print("ID token verification successful")
        
        # Get user info from Google
        print("Getting user info from Google...")
        user_info = await google_oauth_service.get_user_info(tokens["access_token"])
        print(f"User info retrieved: {user_info.get('email', 'No email')}")
        
        # Check if user exists
        print(f"Checking if user exists with Google ID: {user_info['id']}")
        user = db.query(User).filter(User.google_id == user_info["id"]).first()
        
        if not user:
            print("User not found by Google ID, checking by email...")
            # Check if email already exists with different auth method
            existing_user = db.query(User).filter(User.email == user_info["email"]).first()
            if existing_user:
                print("Found existing user by email, linking Google account...")
                # Link Google account to existing user
                existing_user.google_id = user_info["id"]
                existing_user.google_email = user_info["email"]
                existing_user.google_name = user_info.get("name")
                existing_user.google_picture = user_info.get("picture")
                existing_user.auth_method = "both"  # User has both local and Google auth
                user = existing_user
            else:
                print("Creating new user...")
                # Create new user
                user = User(
                    google_id=user_info["id"],
                    google_email=user_info["email"],
                    google_name=user_info.get("name"),
                    google_picture=user_info.get("picture"),
                    email=user_info["email"],
                    username=user_info["email"].split("@")[0],  # Use email prefix as username
                    auth_method="google"
                )
                db.add(user)
        else:
            print("Found existing user by Google ID")
        
        db.commit()
        db.refresh(user)
        print(f"User saved to database. User ID: {user.id}")
        
        # Create access token
        print("Creating access token...")
        token = create_access_token(
            username=user.username or user.google_email, 
            user_id=user.id, 
            expires_delta=timedelta(minutes=20)
        )
        print("Access token created successfully")
        
        return {"access_token": token, "token_type": "bearer"}
        
    except Exception as e:
        print(f"Error in Google callback: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) 