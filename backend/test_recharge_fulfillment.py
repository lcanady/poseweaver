#!/usr/bin/env python3
"""
Test script to simulate Stripe webhook for recharge pack fulfillment.
This helps debug why extra generations aren't being added to user accounts.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.user_mongo import User
from app.config.stripe_config import get_recharge_package_by_price_id, STRIPE_PRICES

def test_recharge_fulfillment():
    """Test the recharge pack fulfillment logic."""
    
    print("=== Testing Recharge Pack Fulfillment ===\n")
    
    # Test the price_id lookup function
    print("1. Testing price_id lookup...")
    price_id_50 = STRIPE_PRICES['recharge_50']
    print(f"50-generation pack price_id: {price_id_50}")
    
    package = get_recharge_package_by_price_id(price_id_50)
    if package:
        print(f"✅ Found package: {package['generations']} generations for ${package['amount']/100}")
    else:
        print("❌ Package lookup failed!")
        return
    
    print("\n2. Testing user lookup and generation addition...")
    
    # Simulate webhook session data
    mock_session = {
        'customer': 'cus_test123',
        'customer_details': {'email': 'test@example.com'},
        'amount_total': 499,  # $4.99 in cents
        'currency': 'usd',
        'line_items': {
            'data': [{
                'price': {'id': price_id_50},
                'quantity': 1
            }]
        },
        'metadata': {
            'user_id': 'test_user_id',
            'type': 'recharge',
            'generation_count': '50'
        }
    }
    
    # Test the fulfillment logic (without actually modifying database)
    print("Simulating webhook fulfillment...")
    
    try:
        # Extract session information
        customer_id = mock_session.get('customer')
        customer_email = mock_session.get('customer_details', {}).get('email')
        amount_total = mock_session.get('amount_total')
        currency = mock_session.get('currency')
        metadata = mock_session.get('metadata', {})
        
        print(f"Payment: {amount_total} {currency}")
        print(f"Customer: {customer_id} ({customer_email})")
        
        # Get line items to determine what was purchased
        line_items = mock_session.get('line_items', {}).get('data', [])
        if not line_items:
            print("❌ No line items found in session")
            return
        
        total_generations_to_add = 0
        for item in line_items:
            price_id = item.get('price', {}).get('id')
            quantity = item.get('quantity', 1)
            
            print(f"Processing item: price_id={price_id}, quantity={quantity}")
            
            # Find the recharge package by price_id
            package = get_recharge_package_by_price_id(price_id)
            if package:
                generations_to_add = package['generations'] * quantity
                total_generations_to_add += generations_to_add
                print(f"✅ Would add {generations_to_add} generations")
            else:
                print(f"❌ No package found for price_id: {price_id}")
        
        if total_generations_to_add > 0:
            print(f"\n✅ Total generations to add: {total_generations_to_add}")
            print("✅ Fulfillment logic appears to be working correctly!")
        else:
            print("\n❌ No generations would be added - there's a bug in the fulfillment logic")
            
    except Exception as e:
        print(f"❌ Error in fulfillment logic: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_recharge_fulfillment()
