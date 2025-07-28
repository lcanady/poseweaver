"""
Stripe configuration and product/price mappings.
"""
import os
import stripe
from typing import Dict, Any, Optional

# Stripe will be initialized when functions are called
# This avoids issues with missing API keys during import

# Stripe Product and Price IDs (created via Stripe API - LIVE)
STRIPE_PRODUCTS = {
    'basic_subscription': 'prod_SlH4efjw4w1zAM',
    'pro_subscription': 'prod_SlH5S5nhZwkfe6',
    'recharge_50': 'prod_SlH5vb5XH0O3Hb',
    'recharge_100': 'prod_SlH5bVyPdcLWYf',
    'recharge_250': 'prod_SlH5W0IKaBOCK7',
    'recharge_500': 'prod_SlH54TVGzxso1d'
}

STRIPE_PRICES = {
    'basic_subscription': 'price_1RpwygPnxX6KbXoKMPthxOpM',  # $9.99 recurring monthly (LIVE)
    'pro_subscription': 'price_1RpwyqPnxX6KbXoKs4CrRKwy',    # $19.99 recurring monthly (LIVE)
    'basic_annual': 'price_1Rpwz1PnxX6KbXoKNClZKC94',        # $99.90 recurring yearly (LIVE)
    'pro_annual': 'price_1RpwzAPnxX6KbXoK8glqkrBX',          # $199.90 recurring yearly (LIVE)
    'recharge_50': 'price_1RpkY3PnxX6KbXoKHKR3nLh5',         # $4.99 (LIVE)
    'recharge_100': 'price_1RpkY3PnxX6KbXoKnIc2YZGu',        # $8.99 (LIVE)
    'recharge_250': 'price_1RpkY4PnxX6KbXoK1o9Heout',        # $19.99 (LIVE)
    'recharge_500': 'price_1RpkY4PnxX6KbXoKtXazQ2MS'         # $34.99 (LIVE)
}

# Recharge pack mappings
RECHARGE_PACKAGES = {
    50: {
        'price_id': STRIPE_PRICES['recharge_50'],
        'product_id': STRIPE_PRODUCTS['recharge_50'],
        'amount': 499,  # $4.99 in cents
        'generations': 50
    },
    100: {
        'price_id': STRIPE_PRICES['recharge_100'],
        'product_id': STRIPE_PRODUCTS['recharge_100'],
        'amount': 899,  # $8.99 in cents
        'generations': 100
    },
    250: {
        'price_id': STRIPE_PRICES['recharge_250'],
        'product_id': STRIPE_PRODUCTS['recharge_250'],
        'amount': 1999,  # $19.99 in cents
        'generations': 250
    },
    500: {
        'price_id': STRIPE_PRICES['recharge_500'],
        'product_id': STRIPE_PRODUCTS['recharge_500'],
        'amount': 3499,  # $34.99 in cents
        'generations': 500
    }
}

# Subscription mappings
SUBSCRIPTION_PLANS = {
    'basic': {
        'price_id': STRIPE_PRICES['basic_subscription'],
        'product_id': STRIPE_PRODUCTS['basic_subscription'],
        'amount': 999,  # $9.99 in cents
        'generations': 200,
        'character_limit': 10,
        'name': 'Basic Monthly'
    },
    'pro': {
        'price_id': STRIPE_PRICES['pro_subscription'],
        'product_id': STRIPE_PRODUCTS['pro_subscription'],
        'amount': 1999,  # $19.99 in cents
        'generations': 500,
        'character_limit': -1,  # Unlimited
        'name': 'Pro Monthly'
    },
    'basic_annual': {
        'price_id': STRIPE_PRICES['basic_annual'],
        'product_id': STRIPE_PRODUCTS['basic_subscription'],
        'amount': 9990,  # $99.90 in cents
        'generations': 200,
        'character_limit': 10,
        'name': 'Basic Annual'
    },
    'pro_annual': {
        'price_id': STRIPE_PRICES['pro_annual'],
        'product_id': STRIPE_PRODUCTS['pro_subscription'],
        'amount': 19990,  # $199.90 in cents
        'generations': 500,
        'character_limit': -1,  # Unlimited
        'name': 'Pro Annual'
    }
}


def get_recharge_package(generation_count: int) -> Dict[str, Any]:
    """Get recharge package info for a specific generation count."""
    return RECHARGE_PACKAGES.get(generation_count)


def get_recharge_package_by_price_id(price_id: str) -> Dict[str, Any]:
    """Get recharge package info for a specific Stripe price ID."""
    for generation_count, package in RECHARGE_PACKAGES.items():
        if package['price_id'] == price_id:
            return package
    return None


def get_subscription_plan(plan_name: str) -> Dict[str, Any]:
    """Get subscription plan info for a specific plan."""
    return SUBSCRIPTION_PLANS.get(plan_name)


def _ensure_stripe_initialized():
    """Ensure Stripe is initialized with API key."""
    stripe_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe_key or stripe_key == 'sk_test_your_stripe_secret_key_here':
        raise ValueError("STRIPE_SECRET_KEY environment variable is not set or is using placeholder value. Please configure your Stripe secret key in the .env file.")
    
    # Always set the API key to ensure it's current
    stripe.api_key = stripe_key
    
    # Verify that stripe.api_key is actually set
    if not stripe.api_key:
        raise ValueError("Failed to initialize Stripe API key")
    
    # Test the API key by making a simple API call
    try:
        # This will fail if the API key is invalid
        stripe.Account.retrieve()
    except stripe.error.AuthenticationError:
        raise ValueError("Invalid Stripe API key. Please check your STRIPE_SECRET_KEY in the .env file.")
    except stripe.error.StripeError as e:
        # Other Stripe errors are acceptable here (like network issues)
        # We just want to verify the API key is valid
        pass


def create_payment_intent(amount: int, currency: str = 'usd', metadata: Optional[Dict[str, str]] = None) -> Any:
    """Create a Stripe PaymentIntent."""
    _ensure_stripe_initialized()
    return stripe.PaymentIntent.create(
        amount=amount,
        currency=currency,
        metadata=metadata or {},
        automatic_payment_methods={'enabled': True}
    )


def create_checkout_session(price_id: str, success_url: str, cancel_url: str, metadata: Optional[Dict[str, str]] = None) -> Any:
    """Create a Stripe Checkout Session."""
    try:
        _ensure_stripe_initialized()
        return stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata or {}
        )
    except ValueError as e:
        # Re-raise ValueError with clear message for Stripe configuration issues
        raise ValueError(f"Stripe configuration error: {str(e)}")
    except Exception as e:
        # Handle other Stripe API errors
        raise Exception(f"Failed to create Stripe checkout session: {str(e)}")


def create_subscription_checkout_session(price_id: str, success_url: str, cancel_url: str, customer_email: Optional[str] = None, metadata: Optional[Dict[str, str]] = None) -> Any:
    """Create a Stripe Checkout Session for subscriptions."""
    try:
        print(f"[DEBUG] Starting subscription checkout session creation...")
        print(f"[DEBUG] price_id: {price_id}")
        print(f"[DEBUG] success_url: {success_url}")
        print(f"[DEBUG] cancel_url: {cancel_url}")
        print(f"[DEBUG] customer_email: {customer_email}")
        print(f"[DEBUG] metadata: {metadata}")
        
        print(f"[DEBUG] Ensuring Stripe is initialized...")
        _ensure_stripe_initialized()
        print(f"[DEBUG] Stripe initialized successfully")
        
        session_data = {
            'payment_method_types': ['card'],
            'line_items': [{
                'price': price_id,
                'quantity': 1,
            }],
            'mode': 'subscription',
            'success_url': success_url,
            'cancel_url': cancel_url,
            'metadata': metadata or {}
        }
        
        if customer_email:
            session_data['customer_email'] = customer_email
        
        print(f"[DEBUG] Session data prepared: {session_data}")
        print(f"[DEBUG] Creating Stripe checkout session...")
        
        session = stripe.checkout.Session.create(**session_data)
        print(f"[DEBUG] Session created successfully: {session.id}")
        return session
        
    except ValueError as e:
        print(f"[DEBUG] ValueError in subscription checkout: {str(e)}")
        # Re-raise ValueError with clear message for Stripe configuration issues
        raise ValueError(f"Stripe configuration error: {str(e)}")
    except Exception as e:
        print(f"[DEBUG] Exception in subscription checkout: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
        # Handle other Stripe API errors
        raise Exception(f"Failed to create Stripe subscription checkout session: {str(e)}")


def retrieve_payment_intent(payment_intent_id: str) -> Any:
    """Retrieve a PaymentIntent from Stripe."""
    _ensure_stripe_initialized()
    return stripe.PaymentIntent.retrieve(payment_intent_id)


def retrieve_checkout_session(session_id: str) -> Any:
    """Retrieve a Checkout Session from Stripe."""
    _ensure_stripe_initialized()
    return stripe.checkout.Session.retrieve(session_id)
