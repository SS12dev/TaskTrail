"""
Pytest configuration and fixtures for TaskTrail tests.

This file is automatically run by pytest before any tests execute,
ensuring proper setup and initialization.
"""

import pytest
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Get absolute paths
backend_path = Path(__file__).parent.parent / "backend"
env_path = backend_path / ".env"

# Load environment variables FIRST before anything else
if env_path.exists():
    load_dotenv(env_path)
else:
    print(f"[CONFTEST] ERROR: .env file not found at {env_path}")

# Add backend to path
sys.path.insert(0, str(backend_path))

# Set environment variable for Firebase service account path (absolute path)
os.environ["FIREBASE_SERVICE_ACCOUNT_PATH"] = str(backend_path / "serviceAccountKey.json")

# Initialize Firebase ONCE before all tests
from app.firebase import initialize_firebase
try:
    initialize_firebase()
except Exception as e:
    print(f"[CONFTEST] Firebase initialization error: {e}")


@pytest.fixture(scope="session")
def firebase_initialized():
    """Ensure Firebase is initialized for the test session."""
    return True


@pytest.fixture
def test_user_token():
    """
    Get test user authentication token from environment.
    
    Note: This should be a REAL Firebase ID token from an authenticated user.
    To get a valid token:
    1. Run: python backend/get_test_token.py
    2. Enter your Firebase user credentials
    3. Token will be saved to backend/.env automatically
    
    Tokens expire after 1 hour - re-run get_test_token.py when expired.
    """
    token = os.getenv("TEST_USER_TOKEN")
    
    if not token or token == "tK6U64EEwrPDtGVAi85Ozv1ngwo2":  # Skip if using placeholder token
        pytest.skip("Valid TEST_USER_TOKEN not set. Run: python backend/get_test_token.py")
    
    return token


@pytest.fixture
def auth_headers(test_user_token):
    """Generate authorization headers with bearer token."""
    return {"Authorization": f"Bearer {test_user_token}"}
