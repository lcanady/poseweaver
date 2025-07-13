#!/usr/bin/env python3
"""
Test script to verify Venice.ai API connection.
Run this script to test your API key before starting the full application.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.venice_client import VeniceClient, VeniceAPIError

def test_venice_connection():
    """Test Venice.ai API connection."""
    try:
        # Get API key from environment
        api_key = os.getenv('VENICE_API_KEY')
        if not api_key:
            print("❌ ERROR: VENICE_API_KEY not found in environment variables")
            print("Please set your Venice.ai API key in backend/.env")
            return False
        
        if api_key == "your_venice_api_key_here":
            print("❌ ERROR: Please replace 'your_venice_api_key_here' with your actual Venice.ai API key")
            print("Edit backend/.env and set VENICE_API_KEY=your_actual_key")
            return False
        
        print("🔑 API key found, testing connection...")
        
        # Create client
        client = VeniceClient(api_key=api_key)
        
        # Test simple completion
        response = client.generate_completion(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, Venice.ai!' in JSON format: {\"message\": \"your_response\"}"}
            ],
            model="venice-uncensored",
            temperature=0.3,
            max_tokens=100
        )
        
        print("✅ SUCCESS: Connected to Venice.ai!")
        print(f"📝 Response: {response}")
        return True
        
    except VeniceAPIError as e:
        print(f"❌ Venice.ai API Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Venice.ai API connection...")
    print("=" * 50)
    
    success = test_venice_connection()
    
    print("=" * 50)
    if success:
        print("✅ Venice.ai connection test PASSED!")
        print("You can now start the application with: make start")
    else:
        print("❌ Venice.ai connection test FAILED!")
        print("Please check your API key and try again.")
    
    sys.exit(0 if success else 1) 