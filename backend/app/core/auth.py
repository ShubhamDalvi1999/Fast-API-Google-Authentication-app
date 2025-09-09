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

# Import from app modules
from app.db.database import get_db
from app.models.models import User
from app.core.google_oauth import google_oauth_service
from app.core.supabase_auth import supabase_auth_service

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
    email: Optional[str] = None
    auth_method: str = "local"
    supabase_id: Optional[str] = None
    supabase_email: Optional[str] = None

class GoogleAuthRequest(BaseModel):
    code: str
    state: str
    nonce: Optional[str] = None

class SupabaseAuthRequest(BaseModel):
    code: str
    state: str

class SupabaseEmailAuthRequest(BaseModel):
    email: str
    password: str

# In-memory storage for OAuth state (use Redis in production)
oauth_states = {}

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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@router.get("/users/me", response_model=UserResponse)
async def get_user(current_user: Annotated[dict, Depends(get_current_user)], db: db_dependency):
    try:
        user = db.query(User).filter(User.id == current_user["id"]).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return {
            "username": user.username,
            "id": user.id,
            "email": user.email if user.email else None,
            "auth_method": user.auth_method,
            "supabase_id": user.supabase_id if user.supabase_id else None,
            "supabase_email": user.supabase_email if user.supabase_email else None
        }
    except Exception as e:
        print(f"Error in get_user: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")

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
        
        db.commit()
        print(f"User saved to database. User ID: {user.id}")
        
        # Create access token
        token = create_access_token(username=user.username, user_id=user.id, expires_delta=timedelta(minutes=20))
        print("Access token created successfully")
        
        return {"access_token": token, "token_type": "bearer"}
        
    except Exception as e:
        print(f"Error in Google callback: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Supabase Authentication endpoints
@router.get("/supabase/authorize")
async def supabase_authorize(provider: str = "google"):
    """Get Supabase OAuth authorization URL"""
    try:
        auth_data = supabase_auth_service.get_authorization_url(provider)
        
        # Store state for validation (use Redis in production)
        oauth_states[auth_data["state"]] = {
            "provider": provider,
            "created_at": datetime.utcnow()
        }
        
        return {
            "authorization_url": auth_data["authorization_url"],
            "state": auth_data["state"],
            "provider": provider
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/supabase/callback", response_model=Token)
async def supabase_callback(supabase_auth: SupabaseAuthRequest, db: db_dependency):
    """Handle Supabase OAuth callback and create/authenticate user"""
    try:
        print(f"Received Supabase callback data: code={supabase_auth.code[:10]}..., state={supabase_auth.state}")
        
        # Validate state parameter
        if supabase_auth.state not in oauth_states:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state parameter"
            )
        
        stored_data = oauth_states[supabase_auth.state]
        provider = stored_data.get("provider", "google")
        
        # Clean up stored state
        del oauth_states[supabase_auth.state]
        
        # Exchange code for tokens
        tokens = await supabase_auth_service.exchange_code_for_tokens(
            supabase_auth.code, 
            supabase_auth.state, 
            "http://localhost:3000/auth/supabase/callback"
        )
        
        # Get user info from Supabase
        user_info = await supabase_auth_service.get_user_info(tokens["access_token"])
        
        # Check if user exists
        user = db.query(User).filter(User.supabase_id == user_info["id"]).first()
        
        if not user:
            # Check if email already exists with different auth method
            existing_user = db.query(User).filter(User.email == user_info["email"]).first()
            if existing_user:
                # Link Supabase account to existing user
                existing_user.supabase_id = user_info["id"]
                existing_user.supabase_email = user_info["email"]
                existing_user.auth_method = "both" if existing_user.auth_method != "supabase" else "supabase"
                user = existing_user
            else:
                # Create new user
                user = User(
                    username=user_info.get("user_metadata", {}).get("full_name", user_info["email"].split("@")[0]),
                    email=user_info["email"],
                    supabase_id=user_info["id"],
                    supabase_email=user_info["email"],
                    auth_method="supabase"
                )
                db.add(user)
            
            db.commit()
            print(f"User saved to database. User ID: {user.id}")
        
        # Create access token
        token = create_access_token(username=user.username, user_id=user.id, expires_delta=timedelta(minutes=20))
        print("Access token created successfully")
        
        return {"access_token": token, "token_type": "bearer"}
        
    except Exception as e:
        print(f"Error in Supabase callback: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/supabase/signup", response_model=Token)
async def supabase_signup(supabase_auth: SupabaseEmailAuthRequest, db: db_dependency):
    """Sign up a new user with Supabase email/password"""
    try:
        # Sign up with Supabase
        result = await supabase_auth_service.sign_up_with_email(
            supabase_auth.email, 
            supabase_auth.password
        )
        
        # Get user info
        user_info = result.get("user", {})
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == supabase_auth.email).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
        
        # Create new user
        user = User(
            username=supabase_auth.email.split("@")[0],
            email=supabase_auth.email,
            supabase_id=user_info.get("id"),
            supabase_email=supabase_auth.email,
            auth_method="supabase"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create access token
        token = create_access_token(username=user.username, user_id=user.id, expires_delta=timedelta(minutes=20))
        
        return {"access_token": token, "token_type": "bearer"}
        
    except Exception as e:
        print(f"Error in Supabase signup: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/supabase/signin", response_model=Token)
async def supabase_signin(supabase_auth: SupabaseEmailAuthRequest, db: db_dependency):
    """Sign in a user with Supabase email/password"""
    try:
        # Sign in with Supabase
        result = await supabase_auth_service.sign_in_with_email(
            supabase_auth.email, 
            supabase_auth.password
        )
        
        # Get user info
        user_info = result.get("user", {})
        
        # Find user in our database
        user = db.query(User).filter(User.supabase_id == user_info.get("id")).first()
        
        if not user:
            # Check if user exists by email
            user = db.query(User).filter(User.email == supabase_auth.email).first()
            if user:
                # Link Supabase account
                user.supabase_id = user_info.get("id")
                user.supabase_email = supabase_auth.email
                user.auth_method = "both" if user.auth_method != "supabase" else "supabase"
            else:
                # Create new user
                user = User(
                    username=supabase_auth.email.split("@")[0],
                    email=supabase_auth.email,
                    supabase_id=user_info.get("id"),
                    supabase_email=supabase_auth.email,
                    auth_method="supabase"
                )
                db.add(user)
                db.commit()
                db.refresh(user)
        
        # Create access token
        token = create_access_token(username=user.username, user_id=user.id, expires_delta=timedelta(minutes=20))
        
        return {"access_token": token, "token_type": "bearer"}
        
    except Exception as e:
        print(f"Error in Supabase signin: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) 

@router.post("/supabase/session", response_model=Token)
async def supabase_session(session_data: dict, db: db_dependency):
    """Handle Supabase session data from frontend OAuth flow"""
    try:
        print(f"Received Supabase session data for user: {session_data.get('user', {}).get('email', 'unknown')}")
        
        user_info = session_data.get("user", {})
        access_token = session_data.get("access_token")
        
        if not user_info or not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session data"
            )
        
        # Check if user exists
        user = db.query(User).filter(User.supabase_id == user_info["id"]).first()
        
        if not user:
            # Check if email already exists with different auth method
            existing_user = db.query(User).filter(User.email == user_info["email"]).first()
            if existing_user:
                # Link Supabase account to existing user
                existing_user.supabase_id = user_info["id"]
                existing_user.supabase_email = user_info["email"]
                existing_user.auth_method = "both" if existing_user.auth_method != "supabase" else "supabase"
                user = existing_user
            else:
                # Create new user
                user = User(
                    username=user_info.get("user_metadata", {}).get("full_name", user_info["email"].split("@")[0]),
                    email=user_info["email"],
                    supabase_id=user_info["id"],
                    supabase_email=user_info["email"],
                    auth_method="supabase"
                )
                db.add(user)
            
            db.commit()
            print(f"User saved to database. User ID: {user.id}")
        
        # Create access token
        token = create_access_token(username=user.username, user_id=user.id, expires_delta=timedelta(minutes=20))
        print("Access token created successfully")
        
        return {"access_token": token, "token_type": "bearer"}
        
    except Exception as e:
        print(f"Error in Supabase session handler: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) 