#!/usr/bin/env python3
"""
Test script to verify Google OAuth endpoint
"""

import requests
import json

def test_google_oauth_endpoint():
    """Test the Google OAuth authorize endpoint"""
    
    url = "http://localhost:8000/api/auth/google/authorize"
    
    try:
        print(f"Testing endpoint: {url}")
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Data: {json.dumps(data, indent=2)}")
            
            # Check if we have the required fields
            if 'authorization_url' in data and 'state' in data:
                print("✅ Google OAuth endpoint is working correctly!")
                print(f"Authorization URL: {data['authorization_url'][:100]}...")
                print(f"State: {data['state']}")
                return True
            else:
                print("❌ Missing required fields in response")
                return False
        else:
            print(f"❌ Request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure the backend is running.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_cors_headers():
    """Test CORS headers"""
    
    url = "http://localhost:8000/api/auth/google/authorize"
    
    try:
        # Test with Origin header to check CORS
        headers = {
            'Origin': 'http://localhost:3000',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        
        print(f"\nCORS Test:")
        print(f"Status Code: {response.status_code}")
        
        # Check for CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        
        print(f"CORS Headers: {cors_headers}")
        
        if response.status_code == 200:
            print("✅ CORS is working correctly!")
            return True
        else:
            print("❌ CORS test failed")
            return False
            
    except Exception as e:
        print(f"❌ CORS test error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Google OAuth endpoint...")
    print("=" * 50)
    
    oauth_ok = test_google_oauth_endpoint()
    cors_ok = test_cors_headers()
    
    print("=" * 50)
    if oauth_ok and cors_ok:
        print("✅ All tests passed! The backend is working correctly.")
        print("\n📝 If you're still getting errors on the frontend:")
        print("1. Check the browser console for JavaScript errors")
        print("2. Make sure the frontend is running on http://localhost:3000")
        print("3. Check if there are any network errors in the browser's Network tab")
    else:
        print("❌ Some tests failed. Please check the errors above.")
