#!/usr/bin/env python
import requests
import json

BASE_URL = "http://localhost:5001"
ACCESS_TOKEN = None

def print_result(name, response):
    print(f"\n--- {name} ---")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def test_endpoint(name, method, endpoint, data=None, headers=None):
    try:
        print(f"Testing {name}...")
        url = f"{BASE_URL}{endpoint}"
        
        # Add Authorization header if we have an access token
        if ACCESS_TOKEN and headers is None:
            headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        elif ACCESS_TOKEN and headers is not None:
            headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"
        
        if method.upper() == "GET":
            r = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            r = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            r = requests.put(url, json=data, headers=headers)
        elif method.upper() == "DELETE":
            r = requests.delete(url, headers=headers)
        else:
            print(f"Unsupported method: {method}")
            return
            
        print_result(name, r)
        return r
    except Exception as e:
        print(f"Error: {e}")
        return None

def register(email, password, display_name):
    print("\n=== USER REGISTRATION ===")
    print(f"Attempting to register user: {email}...")
    
    data = {
        "email": email,
        "password": password,
        "display_name": display_name
    }
    
    response = test_endpoint("Register", "POST", "/api/auth/signup", data=data)
    
    if response and response.status_code == 201:
        print("User registration successful!")
        return True
    else:
        print("User registration failed. User might already exist.")
        return False

def login(email, password):
    global ACCESS_TOKEN
    
    print("\n=== AUTHENTICATION ===")
    print(f"Attempting login with email: {email}...")
    
    data = {
        "email": email,
        "password": password
    }
    
    response = test_endpoint("Login", "POST", "/api/auth/login", data=data)
    
    if response and response.status_code == 200:
        try:
            json_data = response.json()
            ACCESS_TOKEN = json_data.get("access_token")
            print(f"Login successful, access token acquired: {ACCESS_TOKEN[:10]}...")
            return True
        except Exception as e:
            print(f"Failed to parse login response: {e}")
            return False
    else:
        print("Login failed, cannot continue with authenticated tests")
        return False

def run_authenticated_tests():
    # First, test the health endpoint (no auth required)
    print("\n=== HEALTH CHECK ===")
    test_endpoint("Health Check", "GET", "/health")
    
    # Test user credentials
    test_email = "testuser@example.com"
    test_password = "testpass123"
    test_name = "Test User"
    
    # Try to register a test user first
    register_success = register(test_email, test_password, test_name)
    
    # Attempt login with test credentials
    login_success = login(test_email, test_password)
    
    if not login_success:
        print("Authentication failed. Skipping authenticated tests.")
        return
        
    # Now test protected endpoints with authentication
    print("\n=== AUTHENTICATED ENDPOINTS ===")
    
    # Test /api/auth/me endpoint (should now return user info)
    test_endpoint("Current User (Authenticated)", "GET", "/api/auth/me")
    
    # Test character endpoints
    print("\n=== CHARACTER ENDPOINTS ===")
    test_endpoint("List Characters", "GET", "/api/characters")
    test_endpoint("Character Management", "GET", "/api/characters/mgmt")
    
    # Test scene endpoints
    print("\n=== SCENE ENDPOINTS ===")
    test_endpoint("List Scenes", "GET", "/api/scenes")
    
    # Test context endpoints
    print("\n=== CONTEXT ENDPOINTS ===")
    test_endpoint("Get Context", "GET", "/api/context")
    
    # Test model endpoints
    print("\n=== MODEL ENDPOINTS ===")
    test_endpoint("List Models", "GET", "/api/models")
    
    # Test logout (which should invalidate the token)
    print("\n=== LOGOUT TEST ===")
    test_endpoint("Logout", "POST", "/api/auth/logout")
    
    # Try to access an endpoint again (should fail with 401)
    print("\n=== POST-LOGOUT TEST ===")
    test_endpoint("Current User After Logout", "GET", "/api/auth/me")

if __name__ == "__main__":
    print("Starting authenticated API tests...")
    run_authenticated_tests()
    print("\nTests completed.")
