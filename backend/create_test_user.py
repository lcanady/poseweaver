"""
Script to create a test user in the database.
"""
from app.services.auth_service import AuthService
from app import create_app
from app.extensions import init_extensions

# Create Flask app
app = create_app()

# Use app context
with app.app_context():
    # Create test user
    try:
        user = AuthService.register_user(
            email="test@example.com",
            password="password123",
            display_name="Test User"
        )
        print(f"Test user created successfully: {user.id}")
    except ValueError as e:
        print(f"Error creating test user: {e}")
