#!/usr/bin/env python3
"""
Simple script to check environment variables and .env file
"""

import os
from dotenv import load_dotenv

print("🔍 Checking Environment Variables...")
print("=" * 50)

# Check if .env file exists
env_file_path = ".env"
if os.path.exists(env_file_path):
    print(f"✅ .env file found: {env_file_path}")
    
    # Read .env file content
    with open(env_file_path, 'r') as f:
        env_content = f.read()
    
    print(f"📄 .env file content ({len(env_content)} characters):")
    print("-" * 30)
    for line in env_content.split('\n'):
        if line.strip() and not line.strip().startswith('#'):
            # Show only the key, not the value for security
            if '=' in line:
                key = line.split('=')[0].strip()
                print(f"  {key}=[HIDDEN]")
            else:
                print(f"  {line}")
    print("-" * 30)
else:
    print(f"❌ .env file not found: {env_file_path}")

print("\n🔧 Loading environment variables...")
load_dotenv()

# Check specific Supabase variables
supabase_vars = {
    "SUPABASE_URL": os.getenv("SUPABASE_URL"),
    "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY"),
    "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    "SUPABASE_REDIRECT_URI": os.getenv("SUPABASE_REDIRECT_URI")
}

print("\n📋 Supabase Environment Variables:")
for var_name, var_value in supabase_vars.items():
    if var_value:
        # Show first 20 characters for security
        display_value = var_value[:20] + "..." if len(var_value) > 20 else var_value
        print(f"  ✅ {var_name}: {display_value}")
    else:
        print(f"  ❌ {var_name}: Not set")

print("\n🔍 All Environment Variables:")
all_env_vars = {k: v for k, v in os.environ.items() if 'SUPABASE' in k.upper()}
if all_env_vars:
    for var_name, var_value in all_env_vars.items():
        display_value = var_value[:20] + "..." if len(var_value) > 20 else var_value
        print(f"  {var_name}: {display_value}")
else:
    print("  No Supabase-related environment variables found")
