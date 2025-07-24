#!/usr/bin/env python3
"""
Create a test user for paywall testing with proper MongoDB ObjectId.
"""
import os
import sys
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.user_mongo import User
from app.services.mongodb_service import get_mongodb_service

def create_test_user():
    """Create a test user for paywall testing."""
    try:
        # Initialize MongoDB connection
        mongodb_service = get_mongodb_service()
        
        # Check if test user already exists
        existing_user = User.find_by_email('test@example.com')
        if existing_user:
            print(f"Test user already exists with ID: {existing_user.id}")
            return existing_user.id
        
        # Create new test user
        test_user = User(
            email='test@example.com',
            password='testpassword123',
            display_name='Test User',
            bio='Test user for paywall functionality',
            subscription_status='free',
            is_admin=False,
            pose_generations_used=5,  # Start with some usage
            pose_generations_reset_date=datetime.utcnow().replace(day=1),  # Current month
            extra_pose_generations=0
        )
        
        # Save the user
        user_id = test_user.save()
        print(f"Created test user with ID: {user_id}")
        print(f"Email: test@example.com")
        print(f"Password: testpassword123")
        print(f"Subscription: free")
        print(f"Pose generations used: 5/20")
        
        return user_id
        
    except Exception as e:
        print(f"Error creating test user: {e}")
        return None

if __name__ == '__main__':
    user_id = create_test_user()
    if user_id:
        print(f"\nTest user created successfully!")
        print(f"Use this user ID in your frontend: {user_id}")
    else:
        print("Failed to create test user")
