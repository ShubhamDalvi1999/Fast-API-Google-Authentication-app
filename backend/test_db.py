#!/usr/bin/env python3
"""
Test script to verify database connection and Alembic setup
"""

import os
import sys
from sqlalchemy import create_engine, text

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

def test_database_connection():
    """Test if we can connect to the database"""
    try:
        # Use the same database URL as in your app
        database_url = "sqlite:///./database.db"
        print(f"Testing connection to: {database_url}")
        
        engine = create_engine(database_url)
        
        # Test the connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_alembic_config():
    """Test Alembic configuration"""
    try:
        from alembic import context
        from alembic.config import Config
        
        # Load Alembic config
        alembic_cfg = Config("alembic.ini")
        url = alembic_cfg.get_main_option("sqlalchemy.url")
        print(f"✅ Alembic config loaded. Database URL: {url}")
        
        return True
    except Exception as e:
        print(f"❌ Alembic config failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing database setup...")
    print("=" * 50)
    
    db_ok = test_database_connection()
    alembic_ok = test_alembic_config()
    
    print("=" * 50)
    if db_ok and alembic_ok:
        print("✅ All tests passed! You can now run 'alembic upgrade head'")
    else:
        print("❌ Some tests failed. Please check the errors above.")
