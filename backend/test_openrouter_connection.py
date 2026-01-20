#!/usr/bin/env python3
"""
Test script to verify OpenRouter.ai API connection.
Run this script to test your API key before starting the full application.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.openrouter_client import OpenRouterClient, OpenRouterAPIError

def test_openrouter_connection():
    """Test OpenRouter.ai API connection."""
    try:
        # Get API key from environment
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            print("❌ ERROR: OPENROUTER_API_KEY not found in environment variables")
            print("Please set your OpenRouter.ai API key in backend/.env")
            return False
        
        if api_key == "your_openrouter_api_key_here":
            print("❌ ERROR: Please replace 'your_openrouter_api_key_here' with your actual OpenRouter.ai API key")
            print("Edit backend/.env and set OPENROUTER_API_KEY=your_actual_key")
            return False
        
        print("🔑 API key found, testing connection...")
        
        # Create client
        client = OpenRouterClient(api_key=api_key)
        
        # Test simple completion
        response = client.generate_completion(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, OpenRouter.ai!' in JSON format: {\"message\": \"your_response\"}"}
            ],
            model="google/gemini-2.0-flash-001",
            temperature=0.3,
            max_tokens=100
        )
        
        print("✅ SUCCESS: Connected to OpenRouter.ai!")
        print(f"📝 Response: {response}")
        return True
        
    except OpenRouterAPIError as e:
        print(f"❌ OpenRouter.ai API Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing OpenRouter.ai API connection...")
    print("=" * 50)
    
    success = test_openrouter_connection()
    
    print("=" * 50)
    if success:
        print("✅ OpenRouter.ai connection test PASSED!")
        print("You can now start the application with: make start")
    else:
        print("❌ OpenRouter.ai connection test FAILED!")
        print("Please check your API key and try again.")
    
    sys.exit(0 if success else 1) 