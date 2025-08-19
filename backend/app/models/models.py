from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
import sys
import os

# Add the parent directory to sys.path for local development
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
    print(f"Added {parent_dir} to sys.path from models.py")

# Fix imports for different environments
try:
    # Try relative imports first
    from ..db.database import Base
    print("Models: Using relative imports")
except ImportError:
    try:
        # Try absolute imports with backend prefix
        from backend.app.db.database import Base
        print("Models: Using backend.app.* imports")
    except ImportError:
        # Fallback to local imports
        from app.db.database import Base
        print("Models: Using app.* imports")

class User(Base):
    __tablename__ = "users"
    # Add extend_existing to avoid errors when model is imported multiple times
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=True)  # Made nullable for Google OAuth users
    email = Column(String(255), unique=True, nullable=True)  # Added for Google OAuth
    hashed_password = Column(String(100), nullable=True)  # Made nullable for Google OAuth users
    is_active = Column(Boolean, default=True)
    
    # Google OAuth fields
    google_id = Column(String(255), unique=True, nullable=True)
    google_email = Column(String(255), unique=True, nullable=True)
    google_name = Column(String(255), nullable=True)
    google_picture = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Auth method tracking
    auth_method = Column(String(50), default="local")  # "local" or "google" 