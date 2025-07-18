#!/usr/bin/env python3
"""
Test script to verify MongoDB connection and basic operations.
"""
import os
import sys

# Add the backend directory to the Python path
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv  # noqa: E402
from app.services.mongodb_service import get_mongodb_service  # noqa: E402
from app.models.user_mongo import User  # noqa: E402

# Load environment variables
load_dotenv()


def test_mongodb_connection():
    """Test MongoDB connection and basic operations."""
    print("Testing MongoDB connection...")
    
    try:
        # Test connection
        mongodb_service = get_mongodb_service()
        mongodb_service.connect()
        print("✓ Successfully connected to MongoDB")
        
        # Initialize indexes
        User.initialize_indexes()
        print("✓ Initialized user indexes")
        
        # Test basic operations
        test_email = "test@example.com"
        test_password = "testpass123"
        
        # Clean up any existing test user
        existing_user = User.find_by_email(test_email)
        if existing_user:
            existing_user.delete()
            print("✓ Cleaned up existing test user")
        
        # Create a test user
        user = User.create_user(
            email=test_email,
            password=test_password,
            display_name="Test User"
        )
        print(f"✓ Created test user: {user.email}")
        
        # Test authentication
        auth_user = User.authenticate(test_email, test_password)
        if auth_user:
            print("✓ User authentication successful")
        else:
            print("✗ User authentication failed")
            return False
        
        # Test user retrieval
        found_user = User.find_by_email(test_email)
        if found_user:
            print(f"✓ Found user by email: {found_user.email}")
        else:
            print("✗ Failed to find user by email")
            return False
        
        # Test password change
        found_user.set_password("newpassword123")
        found_user.save()
        
        # Verify new password
        if found_user.check_password("newpassword123"):
            print("✓ Password change successful")
        else:
            print("✗ Password change failed")
            return False
        
        # Clean up
        found_user.delete()
        print("✓ Cleaned up test user")
        
        # Disconnect
        mongodb_service.disconnect()
        print("✓ Disconnected from MongoDB")
        
        print("\n🎉 All MongoDB tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ MongoDB test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_mongodb_connection()
    sys.exit(0 if success else 1) 