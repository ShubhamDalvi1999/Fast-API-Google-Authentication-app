import os
import httpx
import secrets
from typing import Dict, Any, Optional
from urllib.parse import urlencode

class SupabaseAuthService:
    def __init__(self):
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_anon_key = os.environ.get("SUPABASE_ANON_KEY")
        self.supabase_service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.supabase_url or not self.supabase_anon_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
    
    def get_authorization_url(self, provider: str = "google") -> Dict[str, str]:
        """Generate Supabase OAuth authorization URL"""
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL not configured")
        
        # Generate a random state parameter for security
        state = secrets.token_urlsafe(32)
        
        # Build the authorization URL
        auth_url = f"{self.supabase_url}/auth/v1/authorize"
        
        # Use the correct redirect URI that matches Supabase configuration
        redirect_uri = "http://localhost:3000/auth/supabase/callback"
        
        params = {
            "provider": provider,
            "redirect_to": redirect_uri,
            "state": state,
            "response_type": "code"
        }
        
        authorization_url = f"{auth_url}?{urlencode(params)}"
        
        return {
            "authorization_url": authorization_url,
            "state": state,
            "provider": provider
        }
    
    async def exchange_code_for_tokens(self, code: str, state: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL not configured")
        
        token_url = f"{self.supabase_url}/auth/v1/token"
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "apikey": self.supabase_anon_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information using access token"""
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL not configured")
        
        user_url = f"{self.supabase_url}/auth/v1/user"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "apikey": self.supabase_anon_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(user_url, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def verify_token(self, access_token: str) -> Dict[str, Any]:
        """Verify if a token is valid"""
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL not configured")
        
        verify_url = f"{self.supabase_url}/auth/v1/user"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "apikey": self.supabase_anon_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(verify_url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                raise ValueError("Invalid token")
    
    async def sign_up_with_email(self, email: str, password: str) -> Dict[str, Any]:
        """Sign up a new user with email and password"""
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL not configured")
        
        signup_url = f"{self.supabase_url}/auth/v1/signup"
        
        data = {
            "email": email,
            "password": password
        }
        
        headers = {
            "Content-Type": "application/json",
            "apikey": self.supabase_anon_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(signup_url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def sign_in_with_email(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in a user with email and password"""
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL not configured")
        
        signin_url = f"{self.supabase_url}/auth/v1/token"
        
        data = {
            "grant_type": "password",
            "email": email,
            "password": password
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "apikey": self.supabase_anon_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(signin_url, data=data, headers=headers)
            response.raise_for_status()
            return response.json()

# Create a global instance
supabase_auth_service = SupabaseAuthService()
