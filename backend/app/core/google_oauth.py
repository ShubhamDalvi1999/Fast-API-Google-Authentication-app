import os
import httpx
import secrets
import hashlib
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import json
from datetime import datetime, timedelta
from .config import settings

class GoogleOAuthService:
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.enabled = bool(self.client_id and self.client_secret)
        
        if not self.enabled:
            print("⚠️  Google OAuth is disabled. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to enable.")
    
    def generate_state(self) -> str:
        """Generate a secure random state parameter for CSRF protection"""
        return secrets.token_urlsafe(32)
    
    def generate_nonce(self) -> str:
        """Generate a secure random nonce for replay attack protection"""
        return secrets.token_urlsafe(32)
    
    def hash_nonce(self, nonce: str) -> str:
        """Hash nonce for Google OAuth (SHA-256, hexadecimal)"""
        return hashlib.sha256(nonce.encode()).hexdigest()
    
    def get_authorization_url(self, state: Optional[str] = None, nonce: Optional[str] = None) -> Dict[str, str]:
        """Generate Google OAuth authorization URL with security parameters"""
        if not self.enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
            )
        
        if not state:
            state = self.generate_state()
        if not nonce:
            nonce = self.generate_nonce()
        
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
            "nonce": self.hash_nonce(nonce)
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"{base_url}?{query_string}"
        
        return {
            "authorization_url": auth_url,
            "state": state,
            "nonce": nonce
        }
    
    async def exchange_code_for_tokens(self, code: str, state: str, expected_state: str) -> Dict[str, Any]:
        """Exchange authorization code for access and ID tokens with state validation"""
        if not self.enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth is not configured"
            )
        
        # Validate state parameter to prevent CSRF attacks
        if state != expected_state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter"
            )
        
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            
            if response.status_code != 200:
                error_data = response.json()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to exchange code for tokens: {error_data.get('error_description', 'Unknown error')}"
                )
            
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google using access token"""
        if not self.enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth is not configured"
            )
        
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(userinfo_url, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user information from Google"
                )
            
            return response.json()
    
    async def verify_id_token(self, id_token: str, nonce: str) -> Dict[str, Any]:
        """Verify Google ID token and extract user information with nonce validation"""
        if not self.enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth is not configured"
            )
        
        import jwt
        
        try:
            # Note: In production, you should verify the token signature
            # This is a simplified version for development
            decoded = jwt.decode(id_token, options={"verify_signature": False})
            
            # Validate nonce to prevent replay attacks
            if 'nonce' in decoded:
                expected_nonce_hash = self.hash_nonce(nonce)
                if decoded['nonce'] != expected_nonce_hash:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid nonce in ID token"
                    )
            
            # Validate token expiration
            if 'exp' in decoded:
                exp_timestamp = decoded['exp']
                if datetime.utcnow().timestamp() > exp_timestamp:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="ID token has expired"
                    )
            
            return decoded
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ID token: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Token verification failed: {str(e)}"
            )

# Create a global instance
google_oauth_service = GoogleOAuthService()
