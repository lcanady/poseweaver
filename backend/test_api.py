#!/usr/bin/env python
import requests
import json

BASE_URL = "http://localhost:5001"

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

def run_tests():
    print("\n=== HEALTH CHECK ===")
    test_endpoint("Health Check", "GET", "/health")
    
    print("\n=== AUTH ENDPOINTS ===")
    test_endpoint("Current User", "GET", "/api/auth/me")
    
    print("\n=== CHARACTER ENDPOINTS ===")
    test_endpoint("List Characters", "GET", "/api/characters")
    test_endpoint("Character Management Options", "GET", "/api/characters/mgmt")
    
    print("\n=== SCENE ENDPOINTS ===")
    test_endpoint("List Scenes", "GET", "/api/scenes")
    
    print("\n=== CONTEXT ENDPOINTS ===")
    test_endpoint("Get Context", "GET", "/api/context")
    
    print("\n=== MODEL ENDPOINTS ===")
    test_endpoint("List Models", "GET", "/api/models")

if __name__ == "__main__":
    print("Starting API tests...")
    run_tests()
    print("\nTests completed.")
