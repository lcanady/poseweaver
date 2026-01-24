"""
Stripe configuration and product/price mappings.
"""
import os
import stripe
from typing import Dict, Any, Optional

# Stripe will be initialized when functions are called
# This avoids issues with missing API keys during import

# Stripe Product and Price IDs (created via Stripe API)
STRIPE_PRODUCTS = {
    'basic_subscription': 'prod_SjX1vdjwGl5SwL',
    'pro_subscription': 'prod_SjX17U04Fl4joF',
    'recharge_50': 'prod_SjX1RFOurYYZ08',
    'recharge_100': 'prod_SjX2mSPYiP5Kfq',
    'recharge_250': 'prod_SjX2W0Ha4DNvbu',
    'recharge_500': 'prod_SjX2ju6mvnO3r2'
}

STRIPE_PRICES = {
    'basic_subscription': 'price_1RoEFDPiG9G5Z3VQQ6Vbuz3X',  # $9.99 recurring
    'pro_subscription': 'price_1RoEFDPiG9G5Z3VQz9JsnHLI',    # $19.99 recurring
    'recharge_50': 'price_1Ro3xqPiG9G5Z3VQbCKkyiS2',         # $4.99
    'recharge_100': 'price_1Ro3yBPiG9G5Z3VQX4n9zw6i',        # $8.99
    'recharge_250': 'price_1Ro3ycPiG9G5Z3VQqnlVLWNg',        # $19.99
    'recharge_500': 'price_1Ro3z3PiG9G5Z3VQMo3LjKz6'         # $34.99
}

# Plugin Products (for one-time plugin purchases)
# These will be created when plugins are added to the marketplace
PLUGIN_PRODUCTS = {
    # Example structure:
    # 'dice_roller_plugin': 'prod_PluginDiceRoller',
    # Add plugin products dynamically or via setup script
}

PLUGIN_PRICES = {
    # Example structure:
    # 'dice_roller_plugin': 'price_PluginDiceRoller',
    # Maps to one-time purchase prices
}


# Recharge pack mappings
RECHARGE_PACKAGES = {
    250: {
        'price_id': STRIPE_PRICES['recharge_50'],  # Mapping old price ID to new higher count
        'product_id': STRIPE_PRODUCTS['recharge_50'],
        'amount': 499,  # $4.99 in cents
        'credits': 250
    },
    750: {
        'price_id': STRIPE_PRICES['recharge_100'],
        'product_id': STRIPE_PRODUCTS['recharge_100'],
        'amount': 899,  # $8.99 in cents
        'credits': 750
    },
    2000: {
        'price_id': STRIPE_PRICES['recharge_250'],
        'product_id': STRIPE_PRODUCTS['recharge_250'],
        'amount': 1999,  # $19.99 in cents
        'credits': 2000
    },
    5000: {
        'price_id': STRIPE_PRICES['recharge_500'],
        'product_id': STRIPE_PRODUCTS['recharge_500'],
        'amount': 3499,  # $34.99 in cents
        'credits': 5000
    }
}

# Subscription mappings
SUBSCRIPTION_PLANS = {
    'basic': {
        'price_id': STRIPE_PRICES['basic_subscription'],
        'product_id': STRIPE_PRODUCTS['basic_subscription'],
        'amount': 999,  # $9.99 in cents
        'credits': 1000,
        'character_limit': 20,
        'name': 'Basic'
    },
    'pro': {
        'price_id': STRIPE_PRICES['pro_subscription'],
        'product_id': STRIPE_PRODUCTS['pro_subscription'],
        'amount': 1999,  # $19.99 in cents
        'credits': 5000,
        'character_limit': -1,  # Unlimited
        'name': 'Pro'
    }
}


def get_recharge_package(credit_count: int) -> Dict[str, Any]:
    """Get recharge package info for a specific credit count."""
    return RECHARGE_PACKAGES.get(credit_count)


def get_recharge_package_by_price_id(price_id: str) -> Dict[str, Any]:
    """Get recharge package info for a specific Stripe price ID."""
    for credit_count, package in RECHARGE_PACKAGES.items():
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


def get_plugin_purchase_info(plugin_manifest) -> Dict[str, Any]:
    """
    Get purchase info for a plugin.
    
    Args:
        plugin_manifest: PluginManifest instance with stripe_price_id and price
    
    Returns:
        Dictionary with price_id, product_id, and amount
    """
    if not plugin_manifest.stripe_price_id:
        # Plugin doesn't have Stripe integration set up yet
        return None
    
    return {
        'price_id': plugin_manifest.stripe_price_id,
        'product_id': plugin_manifest.stripe_product_id,
        'amount': plugin_manifest.price,
    }


def get_plugin_by_price_id(price_id: str):
    """
    Get plugin info by Stripe price ID (for webhook handling).
    
    This should query the PluginManifest collection.
    Returns the plugin or None if not found.
    
    Args:
        price_id: Stripe price ID
    
    Returns:
        PluginManifest instance or None
    """
    from ..models.marketplace import PluginManifest
    from ..extensions import get_db
    
    db = get_db()
    plugin_data = db.find_one(
        PluginManifest.COLLECTION_NAME,
        {'stripe_price_id': price_id}
    )
    
    if plugin_data:
        return PluginManifest.from_dict(plugin_data)
    return None


def create_plugin_checkout_session(
    plugin_manifest,
    user_id: str,
    success_url: str,
    cancel_url: str,
    customer_email: Optional[str] = None
) -> Any:
    """
    Create a Stripe Checkout Session for a one-time plugin purchase.
    
    Args:
        plugin_manifest: PluginManifest instance
        user_id: User ID making the purchase
        success_url: URL to redirect on successful purchase
        cancel_url: URL to redirect on cancelled purchase
        customer_email: Optional customer email
    
    Returns:
        Stripe checkout session
    """
    try:
        _ensure_stripe_initialized()
        
        if not plugin_manifest.stripe_price_id:
            raise ValueError(f"Plugin '{plugin_manifest.name}' does not have Stripe integration configured")
        
        metadata = {
            'user_id': user_id,
            'plugin_id': plugin_manifest.id,
            'purchase_type': 'plugin'
        }
        
        session_data = {
            'payment_method_types': ['card'],
            'line_items': [{
                'price': plugin_manifest.stripe_price_id,
                'quantity': 1,
            }],
            'mode': 'payment',  # One-time payment for plugins
            'success_url': success_url,
            'cancel_url': cancel_url,
            'metadata': metadata
        }
        
        if customer_email:
            session_data['customer_email'] = customer_email
        
        return stripe.checkout.Session.create(**session_data)
        
    except ValueError as e:
        raise ValueError(f"Plugin purchase configuration error: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to create plugin checkout session: {str(e)}")

