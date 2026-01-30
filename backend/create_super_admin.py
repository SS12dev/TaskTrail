"""
Initialize Super Admin

This script creates the first super admin account in Firebase and Firestore.
Run this once during initial setup.

Usage:
    python create_super_admin.py <email> <password>
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import firebase_admin
from firebase_admin import credentials, auth, firestore
from app.dependencies_admin import get_role_permissions
from datetime import datetime


def initialize_firebase():
    """Initialize Firebase Admin SDK."""
    try:
        cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "serviceAccountKey.json")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("✓ Firebase initialized")
    except Exception as e:
        print(f"✗ Firebase initialization failed: {e}")
        sys.exit(1)


def create_super_admin(email: str, password: str):
    """
    Create a super admin user.

    Args:
        email: Admin email address
        password: Admin password (min 8 characters)
    """
    if len(password) < 8:
        print("✗ Password must be at least 8 characters long")
        return False

    try:
        # Create Firebase auth user
        user = auth.create_user(
            email=email,
            password=password,
            email_verified=True,
            display_name="Super Admin"
        )
        
        print(f"✓ Created Firebase auth user: {user.uid}")

        # Create admin document in Firestore
        db = firestore.client()
        admin_ref = db.collection("admins").document(user.uid)
        
        admin_data = {
            "email": email,
            "role": "super_admin",
            "display_name": "Super Admin",
            "permissions": get_role_permissions("super_admin"),
            "created_at": datetime.utcnow(),
            "last_login": None,
            "is_active": True,
            "created_by": "system"
        }
        
        admin_ref.set(admin_data)
        print(f"✓ Created admin document in Firestore")

        # Log the action
        log_ref = db.collection("admin_audit_log").document()
        log_ref.set({
            "admin_id": "system",
            "admin_email": "system",
            "action": "create_super_admin",
            "resource_type": "admin",
            "resource_id": user.uid,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "details": {"email": email},
            "success": True
        })

        print("\n" + "="*60)
        print("✓ SUPER ADMIN CREATED SUCCESSFULLY")
        print("="*60)
        print(f"Email: {email}")
        print(f"UID: {user.uid}")
        print(f"Role: super_admin")
        print("\nYou can now login to the admin panel with these credentials.")
        print("="*60)
        
        return True

    except auth.EmailAlreadyExistsError:
        print(f"✗ User with email {email} already exists in Firebase Auth")
        
        # Check if they're already an admin
        try:
            existing_user = auth.get_user_by_email(email)
            db = firestore.client()
            admin_doc = db.collection("admins").document(existing_user.uid).get()
            
            if admin_doc.exists:
                admin_data = admin_doc.to_dict()
                print(f"✓ User is already an admin with role: {admin_data.get('role')}")
            else:
                print("! User exists but is not an admin. Would you like to promote them? (y/n)")
                response = input().lower()
                if response == 'y':
                    promote_to_admin(existing_user.uid, email)
        except Exception as e:
            print(f"Error checking existing user: {e}")
        
        return False
        
    except Exception as e:
        print(f"✗ Error creating super admin: {e}")
        return False


def promote_to_admin(user_id: str, email: str):
    """Promote an existing user to super admin."""
    try:
        db = firestore.client()
        admin_ref = db.collection("admins").document(user_id)
        
        admin_data = {
            "email": email,
            "role": "super_admin",
            "display_name": "Super Admin",
            "permissions": get_role_permissions("super_admin"),
            "created_at": datetime.utcnow(),
            "last_login": None,
            "is_active": True,
            "promoted_at": datetime.utcnow()
        }
        
        admin_ref.set(admin_data)
        
        print(f"✓ Promoted user {user_id} to super_admin")
        
    except Exception as e:
        print(f"✗ Error promoting user: {e}")


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: python create_super_admin.py <email> <password>")
        print("\nExample:")
        print("  python create_super_admin.py admin@tasktrail.com SecurePassword123!")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]

    print("TaskTrail Super Admin Creation")
    print("="*60)
    print(f"Email: {email}")
    print(f"Password: {'*' * len(password)}")
    print("="*60)
    print("\nInitializing Firebase...")

    initialize_firebase()
    
    print(f"\nCreating super admin account...")
    create_super_admin(email, password)


if __name__ == "__main__":
    main()
