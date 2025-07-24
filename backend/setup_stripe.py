#!/usr/bin/env python3
"""
Stripe Setup Helper Script

This script helps you configure Stripe for the roleplay pose enhancement app.
It will guide you through setting up your Stripe API keys and test the connection.
"""

import os
import sys
import stripe
from dotenv import load_dotenv

def main():
    print("🔧 Stripe Setup Helper")
    print("=" * 50)
    
    # Check if .env file exists
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    env_example_path = os.path.join(os.path.dirname(__file__), '.env.example')
    
    if not os.path.exists(env_path):
        print("❌ .env file not found!")
        print(f"📁 Expected location: {env_path}")
        
        if os.path.exists(env_example_path):
            print("\n💡 Solution:")
            print(f"1. Copy .env.example to .env:")
            print(f"   cp {env_example_path} {env_path}")
            print("2. Edit the .env file and update the Stripe configuration")
            print("3. Run this script again")
        else:
            print("❌ .env.example file also not found!")
            
        return False
    
    # Load environment variables
    load_dotenv(env_path)
    
    # Check Stripe configuration
    stripe_secret = os.getenv('STRIPE_SECRET_KEY')
    stripe_publishable = os.getenv('STRIPE_PUBLISHABLE_KEY')
    stripe_webhook = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    print("🔍 Checking Stripe configuration...")
    
    # Check secret key
    if not stripe_secret or stripe_secret == 'sk_test_your_stripe_secret_key_here':
        print("❌ STRIPE_SECRET_KEY is not configured")
        print("   Please update STRIPE_SECRET_KEY in your .env file")
        print("   Get your secret key from: https://dashboard.stripe.com/apikeys")
        return False
    
    if not stripe_publishable or stripe_publishable == 'pk_test_your_stripe_publishable_key_here':
        print("⚠️  STRIPE_PUBLISHABLE_KEY is not configured")
        print("   This is needed for frontend integration")
        print("   Get your publishable key from: https://dashboard.stripe.com/apikeys")
    
    if not stripe_webhook or stripe_webhook == 'whsec_your_webhook_secret_here':
        print("⚠️  STRIPE_WEBHOOK_SECRET is not configured")
        print("   This is needed for webhook handling")
        print("   Get your webhook secret from: https://dashboard.stripe.com/webhooks")
    
    # Test Stripe connection
    print("\n🧪 Testing Stripe connection...")
    print(f"   Using API key: {stripe_secret[:12]}...{stripe_secret[-4:]}")
    
    try:
        stripe.api_key = stripe_secret
        
        # First, try a simple API call to test authentication
        print("   Testing API authentication...")
        
        # Try a simpler API call first
        try:
            balance = stripe.Balance.retrieve()
            print(f"✅ API key is valid - Balance retrieved successfully")
        except Exception as balance_error:
            print(f"⚠️  Balance API call failed: {balance_error}")
            print("   Trying account retrieval instead...")
        
        account = stripe.Account.retrieve()
        print(f"   Account object type: {type(account)}")
        print(f"   Account object: {account}")
        
        print(f"✅ Successfully connected to Stripe!")
        print(f"   Account ID: {account.id}")
        print(f"   Country: {account.country}")
        print(f"   Currency: {account.default_currency}")
        
        # Check if account has business profile
        if hasattr(account, 'business_profile') and account.business_profile:
            print(f"   Business Name: {account.business_profile.name or 'Not set'}")
        
        # Test product retrieval
        print("\n🛍️  Testing product access...")
        products = stripe.Product.list(limit=5)
        print(f"✅ Found {len(products.data)} products in your Stripe account")
        
        if len(products.data) > 0:
            print("   Products:")
            for product in products.data:
                print(f"   - {product.name} ({product.id})")
        
        # Test checkout session creation (the actual failing operation)
        print("\n🛒 Testing checkout session creation...")
        test_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Test Product',
                    },
                    'unit_amount': 999,  # $9.99
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
        )
        print(f"✅ Test checkout session created: {test_session.id}")
        
        return True
        
    except stripe.error.AuthenticationError:
        print("❌ Authentication failed!")
        print("   Your STRIPE_SECRET_KEY is invalid")
        print("   Please check your API key at: https://dashboard.stripe.com/apikeys")
        return False
        
    except stripe.error.StripeError as e:
        print(f"❌ Stripe API error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def show_next_steps():
    print("\n🚀 Next Steps:")
    print("1. Start your Flask backend server:")
    print("   cd backend && python app.py")
    print("\n2. Test the purchase endpoint:")
    print("   curl -X POST http://localhost:5001/api/purchase/create-checkout-session \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"user_id\":\"test\",\"type\":\"subscription\",\"plan\":\"basic\"}'")
    print("\n3. If you see errors, check the Flask logs for details")

if __name__ == "__main__":
    print("Starting Stripe setup...")
    
    if main():
        print("\n🎉 Stripe setup completed successfully!")
        show_next_steps()
    else:
        print("\n❌ Stripe setup failed. Please fix the issues above and try again.")
        sys.exit(1)
