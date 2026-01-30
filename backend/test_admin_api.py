#!/usr/bin/env python3
"""
Test Admin API Script

Quick script to test admin endpoints after creating super admin.
Usage: python test_admin_api.py <email> <password>
"""

import sys
import requests
import json
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8000/api/v1"
AUTH_BASE = "http://localhost:8000/api/v1/auth"


def print_section(title):
    """Print formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")


def print_result(endpoint, status_code, data):
    """Print formatted API result."""
    status_emoji = "✅" if 200 <= status_code < 300 else "❌"
    print(f"{status_emoji} {endpoint}")
    print(f"Status: {status_code}")
    print(f"Response: {json.dumps(data, indent=2)}\n")


def get_admin_token(email, password):
    """Authenticate and get admin token (requires Firebase setup)."""
    print_section("Authentication")
    print(f"Attempting to authenticate: {email}")
    print("\n⚠️  Note: This requires Firebase Auth REST API.")
    print("For testing, you can also get token from Firebase Console.\n")
    
    # This is a placeholder - in production you'd use Firebase Auth
    # For now, return None and user can paste token
    token = input("Enter admin Firebase ID token (or press Enter to skip): ").strip()
    if token:
        return token
    return None


def test_admin_endpoints(token):
    """Test all admin endpoints."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: List Users
    print_section("1. List Users")
    try:
        response = requests.get(f"{API_BASE}/admin/users", headers=headers)
        print_result("GET /admin/users", response.status_code, response.json())
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
    
    # Test 2: System Overview
    print_section("2. System Analytics")
    try:
        response = requests.get(f"{API_BASE}/admin/analytics/overview", headers=headers)
        print_result("GET /admin/analytics/overview", response.status_code, response.json())
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
    
    # Test 3: Get Configuration
    print_section("3. System Configuration")
    try:
        response = requests.get(f"{API_BASE}/admin/config", headers=headers)
        data = response.json()
        # Mask API key for security
        if "openai" in data and "apiKey" in data["openai"]:
            key = data["openai"]["apiKey"]
            data["openai"]["apiKey"] = f"{key[:10]}...{key[-4:]}" if len(key) > 14 else "***"
        print_result("GET /admin/config", response.status_code, data)
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
    
    # Test 4: Audit Logs
    print_section("4. Audit Logs")
    try:
        response = requests.get(f"{API_BASE}/admin/audit-logs", headers=headers)
        print_result("GET /admin/audit-logs", response.status_code, response.json())
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
    
    # Test 5: Top Users
    print_section("5. Top Users by Token Usage")
    try:
        response = requests.get(
            f"{API_BASE}/admin/analytics/top-users",
            headers=headers,
            params={"metric": "tokens", "limit": 5}
        )
        print_result("GET /admin/analytics/top-users", response.status_code, response.json())
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")


def test_public_endpoints():
    """Test public endpoints (no auth required)."""
    print_section("Public Endpoints")
    
    # Test health check
    try:
        response = requests.get("http://localhost:8000/health")
        print_result("GET /health", response.status_code, response.json())
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
    
    # Test API docs
    try:
        response = requests.get("http://localhost:8000/docs")
        status_emoji = "✅" if response.status_code == 200 else "❌"
        print(f"{status_emoji} GET /docs")
        print(f"Status: {response.status_code}")
        print("API documentation is accessible\n")
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")


def main():
    """Main test function."""
    print("\n" + "="*60)
    print(" TaskTrail Admin API Test Suite")
    print("="*60)
    print(f" Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Target: {API_BASE}")
    print("="*60)
    
    # Test public endpoints first
    test_public_endpoints()
    
    # Check if token provided as argument
    token = None
    if len(sys.argv) > 1:
        email = sys.argv[1]
        password = sys.argv[2] if len(sys.argv) > 2 else None
        
        if password:
            token = get_admin_token(email, password)
        else:
            print("\n⚠️  Password not provided. Skipping authentication.")
    else:
        print("\n📝 Usage: python test_admin_api.py <email> <password>")
        print("Or provide Firebase ID token when prompted.\n")
        token = input("Enter admin Firebase ID token (or press Enter to skip admin tests): ").strip()
    
    # Test admin endpoints if token available
    if token:
        test_admin_endpoints(token)
    else:
        print("\n⚠️  No authentication token provided.")
        print("Admin endpoint tests skipped.\n")
        print("To test admin endpoints:")
        print("1. Get Firebase ID token from Firebase Console")
        print("2. Or authenticate via Firebase Auth REST API")
        print("3. Run: python test_admin_api.py <email> <password>\n")
    
    # Summary
    print_section("Test Complete")
    print("✅ Public endpoints tested")
    if token:
        print("✅ Admin endpoints tested")
    else:
        print("⚠️  Admin endpoints skipped (no auth token)")
    print("\nNext steps:")
    print("1. Check API docs: http://localhost:8000/docs")
    print("2. Review admin guide: docs/ADMIN_DASHBOARD_GUIDE.md")
    print("3. Test frontend: http://localhost:5173")
    print("4. Test admin UI: http://localhost:3001\n")


if __name__ == "__main__":
    main()
