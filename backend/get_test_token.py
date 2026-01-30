"""
Get Firebase ID Token for Testing

This script authenticates with Firebase using email/password and retrieves
an ID token that can be used for testing authenticated endpoints.
"""

import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv, set_key

# Load environment to get Firebase config
load_dotenv()

# Firebase Web API Key (from Firebase Console → Project Settings → Web API Key)
FIREBASE_WEB_API_KEY = "AIzaSyBZhitUZ98JYTX3EQWkOkcH-yfaf_TRTZQ"

def get_firebase_token(email: str, password: str) -> dict:
    """
    Get Firebase ID token using email and password.
    
    Args:
        email: User's email address
        password: User's password
        
    Returns:
        Dict containing idToken, refreshToken, and expiresIn
    """
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        error_data = response.json()
        error_message = error_data.get("error", {}).get("message", "Unknown error")
        raise Exception(f"Authentication failed: {error_message}")


def save_token_to_env(token: str):
    """Save token to .env file."""
    env_file = Path(__file__).parent / ".env"
    set_key(env_file, "TEST_USER_TOKEN", token)
    print(f"✅ Token saved to {env_file}")


def main():
    """Main function to get and save Firebase token."""
    print("=" * 60)
    print("Firebase Test Token Generator")
    print("=" * 60)
    print("\nThis will sign in to Firebase and save the ID token to .env")
    print("for use in automated tests.\n")
    
    # Get credentials
    email = input("Enter test user email: ").strip()
    password = input("Enter test user password: ").strip()
    
    if not email or not password:
        print("❌ Email and password are required!")
        return
    
    try:
        print("\n🔐 Authenticating with Firebase...")
        result = get_firebase_token(email, password)
        
        id_token = result["idToken"]
        expires_in = result["expiresIn"]
        
        print(f"✅ Authentication successful!")
        print(f"📝 Token will expire in {int(expires_in) // 3600} hour(s)")
        print(f"\nToken (first 50 chars): {id_token[:50]}...")
        
        # Save to .env
        save_token_to_env(id_token)
        
        print("\n✅ Done! You can now run tests with:")
        print("   cd tests")
        print("   python run_tests.py -v")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure the email/password are correct")
        print("2. Check that the user exists in Firebase Console")
        print("3. Verify FIREBASE_WEB_API_KEY is correct in this script")


if __name__ == "__main__":
    main()
