"""
Purchase API endpoints for extra pose generations and subscription upgrades.
"""
from flask import Blueprint, request, jsonify
from ..config.stripe_config import STRIPE_PRICES, create_checkout_session
from ..models.user_mongo import User
import stripe
import os
from ..services.usage_tracking_service import UsageTrackingService
from ..config.stripe_config import (
    get_recharge_package, 
    get_recharge_package_by_price_id,
    get_subscription_plan,
    create_checkout_session,
    create_subscription_checkout_session,
    retrieve_checkout_session,
    RECHARGE_PACKAGES,
    SUBSCRIPTION_PLANS
)

purchase_bp = Blueprint('purchase', __name__)

# Stripe will be initialized when needed via _ensure_stripe_initialized()


@purchase_bp.route('/create-checkout-session', methods=['POST'])
def create_checkout_session_endpoint():
    """Create a Stripe checkout session for recharge packs or subscriptions.
    
    Request body:
    {
        "user_id": "user-id-here",
        "type": "recharge" | "subscription",
        "generation_count": 50,  // For recharge packs
        "plan": "basic" | "pro",  // For subscriptions
        "success_url": "https://yourapp.com/success",
        "cancel_url": "https://yourapp.com/cancel"
    }
    
    Returns:
    {
        "success": true,
        "checkout_url": "https://checkout.stripe.com/...",
        "session_id": "cs_..."
    }
    """
    try:
        data = request.get_json(force=True, silent=True)
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Get user
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'user_id is required'
            }), 400
        
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        purchase_type = data.get('type')
        success_url = data.get('success_url', 'http://localhost:3000/success?session_id={CHECKOUT_SESSION_ID}')
        cancel_url = data.get('cancel_url', 'http://localhost:3000/cancel')
        
        if purchase_type == 'recharge':
            # Handle recharge pack purchase
            generation_count = data.get('generation_count')
            if not generation_count:
                return jsonify({
                    'success': False,
                    'error': 'generation_count is required for recharge packs'
                }), 400
            
            # Check if user can purchase extra generations
            if not user.can_purchase_extra_generations():
                return jsonify({
                    'success': False,
                    'error': 'Only premium subscribers can purchase additional generations',
                    'error_code': 'PREMIUM_REQUIRED'
                }), 403
            
            recharge_package = get_recharge_package(generation_count)
            if not recharge_package:
                return jsonify({
                    'success': False,
                    'error': f'Invalid generation count: {generation_count}. Available: 50, 100, 250, 500'
                }), 400
            
            # Create checkout session for recharge pack
            session = create_checkout_session(
                price_id=recharge_package['price_id'],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': user_id,
                    'type': 'recharge',
                    'generation_count': str(generation_count)
                }
            )
            
        elif purchase_type == 'subscription':
            # Handle subscription purchase
            plan = data.get('plan')
            if not plan or plan not in ['basic', 'pro']:
                return jsonify({
                    'success': False,
                    'error': 'plan must be "basic" or "pro"'
                }), 400
            
            subscription_plan = get_subscription_plan(plan)
            if not subscription_plan:
                return jsonify({
                    'success': False,
                    'error': f'Invalid subscription plan: {plan}'
                }), 400
            
            # Create checkout session for subscription
            session = create_subscription_checkout_session(
                price_id=subscription_plan['price_id'],
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=user.email if hasattr(user, 'email') else None,
                metadata={
                    'user_id': user_id,
                    'type': 'subscription',
                    'plan': plan
                }
            )
            
        else:
            return jsonify({
                'success': False,
                'error': 'type must be "recharge" or "subscription"'
            }), 400
        
        return jsonify({
            'success': True,
            'checkout_url': session.url,
            'session_id': session.id
        })
        
    except ValueError as e:
        # Handle Stripe configuration errors
        error_msg = str(e)
        if "STRIPE_SECRET_KEY" in error_msg or "Stripe configuration error" in error_msg:
            return jsonify({
                'success': False,
                'error': f'Stripe not configured: {error_msg}',
                'error_code': 'STRIPE_CONFIG_ERROR',
                'setup_instructions': 'Please set your STRIPE_SECRET_KEY in the .env file. Copy .env.example to .env and update the Stripe configuration.'
            }), 500
        else:
            return jsonify({
                'success': False,
                'error': f'Validation error: {str(e)}'
            }), 400
        
    except stripe.error.StripeError as e:
        return jsonify({
            'success': False,
            'error': f'Stripe error: {str(e)}'
        }), 402
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@purchase_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events (supports both regular and thin payloads)."""
    print(f"[WEBHOOK DEBUG] Received webhook request")
    print(f"[WEBHOOK DEBUG] Request method: {request.method}")
    print(f"[WEBHOOK DEBUG] Content-Type: {request.headers.get('Content-Type')}")
    print(f"[WEBHOOK DEBUG] Headers: {dict(request.headers)}")
    
    # Get raw payload
    payload = request.get_data(as_text=True)
    print(f"[WEBHOOK DEBUG] Payload length: {len(payload) if payload else 0}")
    print(f"[WEBHOOK DEBUG] Payload preview: {payload[:200] if payload else 'None'}...")
    
    # Get signature header
    sig_header = request.headers.get('Stripe-Signature')
    print(f"[WEBHOOK DEBUG] Stripe-Signature header: {sig_header}")
    
    # Get webhook secret
    endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    print(f"[WEBHOOK DEBUG] Webhook secret configured: {bool(endpoint_secret)}")
    print(f"[WEBHOOK DEBUG] Webhook secret preview: {endpoint_secret[:10] if endpoint_secret else 'None'}...")
    
    # Check for missing requirements
    if not payload:
        print(f"[WEBHOOK ERROR] No payload received")
        return jsonify({'error': 'No payload received'}), 400
    
    if not sig_header:
        print(f"[WEBHOOK ERROR] No Stripe-Signature header")
        return jsonify({'error': 'No Stripe-Signature header'}), 400
    
    if not endpoint_secret:
        print(f"[WEBHOOK ERROR] STRIPE_WEBHOOK_SECRET not configured")
        return jsonify({'error': 'Webhook secret not configured'}), 400
    
    # Initialize Stripe
    try:
        from ..config.stripe_config import _ensure_stripe_initialized
        _ensure_stripe_initialized()
        print(f"[WEBHOOK DEBUG] Stripe initialized successfully")
    except Exception as e:
        print(f"[WEBHOOK ERROR] Failed to initialize Stripe: {e}")
        return jsonify({'error': f'Stripe initialization failed: {str(e)}'}), 400
    
    # Verify webhook signature
    try:
        print(f"[WEBHOOK DEBUG] Attempting to construct event from webhook")
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        print(f"[WEBHOOK DEBUG] Event constructed successfully: {event.get('type')}")
    except ValueError as e:
        print(f"[WEBHOOK ERROR] Invalid payload: {e}")
        return jsonify({'error': f'Invalid payload: {str(e)}'}), 400
    except stripe.error.SignatureVerificationError as e:
        print(f"[WEBHOOK ERROR] Invalid signature: {e}")
        return jsonify({'error': f'Invalid signature: {str(e)}'}), 400
    except Exception as e:
        print(f"[WEBHOOK ERROR] Unexpected error during event construction: {e}")
        return jsonify({'error': f'Webhook processing error: {str(e)}'}), 400
    
    # Check if this is a thin payload (minimal data)
    is_thin_payload = _is_thin_payload(event)
    
    # Handle the event based on type
    if event['type'] == 'checkout.session.completed':
        session_data = _get_full_session_data(event, is_thin_payload)
        if session_data:
            # Check if this is a subscription or recharge purchase
            metadata = session_data.get('metadata', {})
            purchase_type = metadata.get('type')
            
            if purchase_type == 'subscription':
                handle_subscription_checkout_completed(session_data)
            elif purchase_type == 'recharge':
                handle_successful_payment(session_data)
    elif event['type'] == 'invoice.payment_succeeded':
        invoice_data = _get_full_invoice_data(event, is_thin_payload)
        if invoice_data:
            handle_subscription_payment(invoice_data)
    elif event['type'] == 'payment_intent.succeeded':
        payment_intent_data = _get_full_payment_intent_data(event, is_thin_payload)
        if payment_intent_data:
            handle_payment_intent_success(payment_intent_data)
    elif event['type'] == 'invoice.payment_failed':
        invoice_data = _get_full_invoice_data(event, is_thin_payload)
        if invoice_data:
            handle_payment_failure(invoice_data)
    elif event['type'] == 'customer.subscription.created':
        subscription_data = _get_full_subscription_data(event, is_thin_payload)
        if subscription_data:
            handle_subscription_created(subscription_data)
    elif event['type'] == 'customer.subscription.updated':
        subscription_data = _get_full_subscription_data(event, is_thin_payload)
        if subscription_data:
            handle_subscription_updated(subscription_data)
    elif event['type'] == 'customer.subscription.deleted':
        subscription_data = _get_full_subscription_data(event, is_thin_payload)
        if subscription_data:
            handle_subscription_deleted(subscription_data)

    return jsonify({'success': True})


def _is_thin_payload(event):
    """Check if the webhook payload is a thin payload.
    
    Thin payloads have minimal data in the 'object' field and require
    additional API calls to fetch full details.
    """
    try:
        event_object = event.get('data', {}).get('object', {})
        
        # Thin payloads typically have very few fields in the object
        # Regular payloads have many more fields with full data
        if event['type'] == 'checkout.session.completed':
            # Regular session objects have metadata, line_items, etc.
            # Thin payloads only have basic fields like id, object type
            return len(event_object.keys()) < 10
        elif event['type'] == 'invoice.payment_succeeded':
            # Regular invoice objects have customer, subscription, lines, etc.
            return len(event_object.keys()) < 15
        elif event['type'] == 'payment_intent.succeeded':
            # Regular payment intent objects have charges, metadata, etc.
            return len(event_object.keys()) < 10
        elif event['type'].startswith('customer.subscription.'):
            # Regular subscription objects have customer, items, plan, etc.
            return len(event_object.keys()) < 12
        
        # Default to assuming regular payload if unsure
        return False
    except Exception:
        # If we can't determine, assume regular payload
        return False


def _get_full_session_data(event, is_thin_payload):
    """Get full checkout session data, fetching from API if thin payload."""
    try:
        if is_thin_payload:
            # Fetch full session data from Stripe API
            session_id = event['data']['object']['id']
            session = stripe.checkout.Session.retrieve(
                session_id,
                expand=['line_items']
            )
            return session
        else:
            # Use data from regular payload
            return event['data']['object']
    except Exception as e:
        print(f"Error fetching full session data: {e}")
        return None


def _get_full_invoice_data(event, is_thin_payload):
    """Get full invoice data, fetching from API if thin payload."""
    try:
        if is_thin_payload:
            # Fetch full invoice data from Stripe API
            invoice_id = event['data']['object']['id']
            invoice = stripe.Invoice.retrieve(
                invoice_id,
                expand=['lines', 'customer', 'subscription']
            )
            return invoice
        else:
            # Use data from regular payload
            return event['data']['object']
    except Exception as e:
        print(f"Error fetching full invoice data: {e}")
        return None


def _get_full_payment_intent_data(event, is_thin_payload):
    """Get full payment intent data, fetching from API if thin payload."""
    try:
        if is_thin_payload:
            # Fetch full payment intent data from Stripe API
            payment_intent_id = event['data']['object']['id']
            payment_intent = stripe.PaymentIntent.retrieve(
                payment_intent_id,
                expand=['charges']
            )
            return payment_intent
        else:
            # Use data from regular payload
            return event['data']['object']
    except Exception as e:
        print(f"Error fetching full payment intent data: {e}")
        return None


def _get_full_subscription_data(event, is_thin_payload):
    """Get full subscription data, fetching from API if thin payload."""
    try:
        if is_thin_payload:
            # Fetch full subscription data from Stripe API
            subscription_id = event['data']['object']['id']
            subscription = stripe.Subscription.retrieve(
                subscription_id,
                expand=['customer', 'items', 'latest_invoice']
            )
            return subscription
        else:
            # Use data from regular payload
            return event['data']['object']
    except Exception as e:
        print(f"Error fetching full subscription data: {e}")
        return None


def handle_subscription_checkout_completed(session):
    """Handle successful subscription checkout completion."""
    try:
        print(f"[DEBUG] Handling subscription checkout completion for session: {session.get('id')}")
        
        metadata = session.get('metadata', {})
        user_id = metadata.get('user_id')
        purchase_type = metadata.get('type')
        plan = metadata.get('plan')
        
        print(f"[DEBUG] Metadata - user_id: {user_id}, type: {purchase_type}, plan: {plan}")
        
        if not user_id or purchase_type != 'subscription' or not plan:
            print(f"[DEBUG] Missing required metadata for subscription upgrade")
            return
        
        user = User.find_by_id(user_id)
        if not user:
            print(f"[DEBUG] User not found: {user_id}")
            return
        
        print(f"[DEBUG] Found user: {user.email}")
        
        # Get subscription info from Stripe
        subscription_id = None
        customer_id = session.get('customer')
        if customer_id:
            # Store the Stripe customer ID for future reference
            user.stripe_customer_id = customer_id
            
            # Get the subscription ID from the session
            if hasattr(session, 'subscription') and session.subscription:
                subscription_id = session.subscription
            
        print(f"[DEBUG] Customer ID: {customer_id}, Subscription ID: {subscription_id}")
        
        # Upgrade user to subscription tier
        if plan in ['basic', 'pro']:
            user.upgrade_to_subscription(plan, subscription_id)
            print(f"[DEBUG] Successfully upgraded user {user.email} to {plan} subscription")
        else:
            print(f"[DEBUG] Invalid subscription plan: {plan}")
        
    except Exception as e:
        print(f"Error handling subscription checkout completion: {e}")
        import traceback
        traceback.print_exc()





def handle_subscription_payment(invoice):
    """Handle successful subscription payment."""
    try:
        # Handle recurring subscription payments
        customer_id = invoice.get('customer')
        subscription_id = invoice.get('subscription')
        amount_paid = invoice.get('amount_paid')
        currency = invoice.get('currency')
        
        if not customer_id:
            print("No customer ID in invoice")
            return
        
        print(f"Subscription payment succeeded for customer: {customer_id}")
        print(f"Subscription ID: {subscription_id}")
        print(f"Amount paid: {amount_paid} {currency}")
        
        # Find user by Stripe customer ID
        user = User.find_by_stripe_customer_id(customer_id)
        if not user:
            print(f"Could not find user for Stripe customer {customer_id}")
            return
        
        # Activate/renew subscription and reset monthly generations
        user.activate_subscription()
        user.reset_monthly_generations()
        
        print(f"Successfully renewed subscription for user {user.email}")
        
    except Exception as e:
        print(f"Error handling subscription payment: {e}")


def handle_payment_intent_success(payment_intent):
    """Handle successful payment intent (additional confirmation)."""
    try:
        # Payment intents can provide additional confirmation for payments
        payment_intent_id = payment_intent.get('id')
        amount = payment_intent.get('amount')
        currency = payment_intent.get('currency')
        metadata = payment_intent.get('metadata', {})
        
        print(f"Payment intent succeeded: {payment_intent_id}")
        print(f"Amount: {amount} {currency}")
        
        # Check if this payment intent has metadata linking it to a user/purchase
        user_id = metadata.get('user_id')
        purchase_type = metadata.get('type')
        
        if user_id and purchase_type:
            print(f"Payment intent for user {user_id}, type: {purchase_type}")
            # Additional processing if needed
        
    except Exception as e:
        print(f"Error handling payment intent success: {e}")


def handle_payment_failure(invoice):
    """Handle failed subscription payment."""
    try:
        customer_id = invoice.get('customer')
        subscription_id = invoice.get('subscription')
        amount_due = invoice.get('amount_due')
        currency = invoice.get('currency')
        attempt_count = invoice.get('attempt_count', 1)
        
        print(f"Payment failed for customer: {customer_id}")
        print(f"Subscription: {subscription_id}")
        print(f"Amount due: {amount_due} {currency}")
        print(f"Attempt: {attempt_count}")
        
        if not customer_id:
            print("No customer ID in failed payment")
            return
        
        # Find user by Stripe customer ID
        user = User.find_by_stripe_customer_id(customer_id)
        if not user:
            print(f"Could not find user for Stripe customer {customer_id}")
            return
        
        # Handle payment failure based on attempt count
        if attempt_count >= 3:
            # Final attempt failed - suspend subscription
            print(f"Final payment attempt failed for user {user.email} - suspending subscription")
            user.suspend_subscription()
            # TODO: Send final notice email
        else:
            # Set grace period for retry attempts
            print(f"Payment attempt {attempt_count} failed for user {user.email} - setting grace period")
            user.set_subscription_grace_period()
            # TODO: Send payment retry notification email
        
        print(f"Handled payment failure for user {user.email}")
        
    except Exception as e:
        print(f"Error handling payment failure: {e}")


def handle_subscription_created(subscription):
    """Handle new subscription creation."""
    try:
        subscription_id = subscription.get('id')
        customer_id = subscription.get('customer')
        status = subscription.get('status')
        items = subscription.get('items', {}).get('data', [])
        
        print(f"New subscription created: {subscription_id}")
        print(f"Customer: {customer_id}")
        print(f"Status: {status}")
        
        if not customer_id or not items:
            print("Missing customer ID or subscription items")
            return
        
        # Get the price ID to determine subscription tier
        price_id = items[0].get('price', {}).get('id') if items else None
        
        # Determine subscription tier based on price ID
        subscription_tier = None
        if price_id == STRIPE_PRICES['basic_subscription']:
            subscription_tier = 'basic'
        elif price_id == STRIPE_PRICES['pro_subscription']:
            subscription_tier = 'pro'
        
        print(f"Subscription tier: {subscription_tier}")
        
        # Find user by Stripe customer ID
        user = User.find_by_stripe_customer_id(customer_id)
        if not user:
            print(f"Could not find user for Stripe customer {customer_id}")
            return
        
        # Upgrade user to subscription tier
        if subscription_tier:
            user.upgrade_to_subscription(subscription_tier, subscription_id)
            print(f"Successfully upgraded user {user.email} to {subscription_tier} subscription")
        else:
            print(f"Could not determine subscription tier for price ID: {price_id}")
        
    except Exception as e:
        print(f"Error handling subscription creation: {e}")


def handle_subscription_updated(subscription):
    """Handle subscription updates (plan changes, status changes)."""
    try:
        subscription_id = subscription.get('id')
        customer_id = subscription.get('customer')
        status = subscription.get('status')
        items = subscription.get('items', {}).get('data', [])
        previous_attributes = subscription.get('previous_attributes', {})
        
        print(f"Subscription updated: {subscription_id}")
        print(f"Customer: {customer_id}")
        print(f"New status: {status}")
        print(f"Previous attributes: {previous_attributes}")
        
        if not customer_id:
            print("No customer ID in subscription update")
            return
        
        # Check if the plan changed
        if 'items' in previous_attributes:
            price_id = items[0].get('price', {}).get('id') if items else None
            
            # Determine new subscription tier
            new_tier = None
            if price_id == STRIPE_PRICES['basic_subscription']:
                new_tier = 'basic'
            elif price_id == STRIPE_PRICES['pro_subscription']:
                new_tier = 'pro'
            
            if new_tier:
                print(f"Plan changed to: {new_tier}")
                # Find user and update subscription tier
                user = User.find_by_stripe_customer_id(customer_id)
                if user:
                    user.update_subscription_tier(new_tier)
                    print(f"Updated user {user.email} to {new_tier} tier")
                else:
                    print(f"Could not find user for Stripe customer {customer_id}")
        
        # Check if status changed
        if 'status' in previous_attributes:
            old_status = previous_attributes['status']
            print(f"Status changed from {old_status} to {status}")
            
            # Handle status changes
            user = User.find_by_stripe_customer_id(customer_id)
            if user:
                if status == 'active':
                    user.activate_subscription()
                    print(f"Activated subscription for user {user.email}")
                elif status in ['past_due', 'unpaid']:
                    user.set_subscription_grace_period()
                    print(f"Set grace period for user {user.email} due to {status} status")
                elif status == 'canceled':
                    user.cancel_subscription()
                    print(f"Canceled subscription for user {user.email}")
            else:
                print(f"Could not find user for Stripe customer {customer_id}")
        
    except Exception as e:
        print(f"Error handling subscription update: {e}")


def handle_subscription_deleted(subscription):
    """Handle subscription cancellation/deletion."""
    try:
        subscription_id = subscription.get('id')
        customer_id = subscription.get('customer')
        status = subscription.get('status')
        canceled_at = subscription.get('canceled_at')
        
        print(f"Subscription deleted: {subscription_id}")
        print(f"Customer: {customer_id}")
        print(f"Final status: {status}")
        print(f"Canceled at: {canceled_at}")
        
        if not customer_id:
            print("No customer ID in subscription deletion")
            return
        
        # Find user by Stripe customer ID
        user = User.find_by_stripe_customer_id(customer_id)
        if not user:
            print(f"Could not find user for Stripe customer {customer_id}")
            return
        
        # Cancel subscription and revert to free tier
        user.cancel_subscription()
        user.revert_to_free_tier()
        print(f"Successfully canceled subscription for user {user.email}")
        
        # TODO: Send cancellation confirmation email
        # TODO: Offer feedback survey about why they canceled
        # TODO: Set up re-engagement email sequence
        
    except Exception as e:
        print(f"Error handling subscription deletion: {e}")


def handle_successful_payment(session):
    """Handle successful one-time payment (recharge packs)."""
    try:
        # Extract session information
        customer_id = session.get('customer')
        customer_email = session.get('customer_details', {}).get('email')
        amount_total = session.get('amount_total')  # in cents
        currency = session.get('currency')
        metadata = session.get('metadata', {})
        
        print(f"Successful payment: {amount_total} {currency}")
        print(f"Customer: {customer_id} ({customer_email})")
        
        # Try to find user by Stripe customer ID first
        user = None
        if customer_id:
            user = User.find_by_stripe_customer_id(customer_id)
        
        # If not found by customer ID, try by email from metadata or customer details
        if not user:
            user_email = metadata.get('user_email') or customer_email
            if user_email:
                user = User.find_by_email(user_email)
                # Link the Stripe customer ID to the user
                if user and customer_id:
                    user.set_stripe_customer_id(customer_id)
        
        if not user:
            print(f"Could not find user for customer {customer_id} or email {customer_email}")
            return
        
        # Get line items to determine what was purchased
        line_items = session.get('line_items', {}).get('data', [])
        if not line_items:
            print("No line items found in session")
            return
        
        total_generations_added = 0
        for item in line_items:
            price_id = item.get('price', {}).get('id')
            quantity = item.get('quantity', 1)
            
            # Find the recharge package by price_id
            package = get_recharge_package_by_price_id(price_id)
            if package:
                generations_to_add = package['generations'] * quantity
                user.add_extra_pose_generations(generations_to_add)
                total_generations_added += generations_to_add
                print(f"Added {generations_to_add} generations to user {user.email}")
        
        if total_generations_added > 0:
            print(f"Successfully added {total_generations_added} total generations to user {user.email}")
        
    except Exception as e:
        print(f"Error handling successful payment: {e}")


@purchase_bp.route('/pricing', methods=['GET'])
def get_pricing():
    """Get pricing information for extra generations and subscriptions with Stripe IDs.
    
    Returns:
    {
        "success": true,
        "extra_generations": {
            "packages": [
                {
                    "generation_count": 50,
                    "price": 4.99,
                    "price_id": "price_...",
                    "product_id": "prod_..."
                }
            ]
        },
        "subscriptions": {
            "basic": {
                "name": "Basic",
                "price": 9.99,
                "price_id": "price_...",
                "product_id": "prod_..."
            }
        }
    }
    """
    try:
        # Build recharge packages with Stripe IDs
        recharge_packages = []
        for count, package in RECHARGE_PACKAGES.items():
            price_per_gen = package['amount'] / 100 / count
            savings = None
            if count == 100:
                savings = '10%'
            elif count == 250:
                savings = '20%'
            elif count == 500:
                savings = '30%'
            
            recharge_packages.append({
                'generation_count': count,
                'price': package['amount'] / 100,  # Convert cents to dollars
                'price_per_generation': round(price_per_gen, 2),
                'price_id': package['price_id'],
                'product_id': package['product_id'],
                'savings': savings,
                'best_value': count == 500
            })
        
        # Sort by generation count
        recharge_packages.sort(key=lambda x: x['generation_count'])
        
        # Build subscription plans with Stripe IDs
        subscriptions = {}
        for plan_key, plan_data in SUBSCRIPTION_PLANS.items():
            subscriptions[plan_key] = {
                'name': plan_data['name'],
                'price': plan_data['amount'] / 100,  # Convert cents to dollars
                'generations_included': plan_data['generations'],
                'character_limit': plan_data['character_limit'],
                'price_id': plan_data['price_id'],
                'product_id': plan_data['product_id'],
                'features': [
                    f"{plan_data['generations']} pose generations per month",
                    'Unlimited character profiles' if plan_data['character_limit'] == -1 else f"Up to {plan_data['character_limit']} character profiles",
                    'All enhancement styles',
                    'Purchase additional generations when needed'
                ],
                'popular': plan_key == 'pro'
            }
            
            # Add extra features for Pro
            if plan_key == 'pro':
                subscriptions[plan_key]['features'].insert(-1, 'Priority support')
        
        return jsonify({
            'success': True,
            'extra_generations': {
                'packages': recharge_packages
            },
            'subscriptions': subscriptions,
            'free_tier': {
                'generations_included': 20,
                'character_limit': 3,
                'features': [
                    '20 pose generations per month',
                    'Up to 3 character profiles',
                    'Basic enhancement options'
                ]
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@purchase_bp.route('/usage-status', methods=['GET'])
def get_usage_status():
    """Get current usage status for a user.
    
    Query params:
    - user_id: User ID to check usage for
    
    Returns:
    {
        "success": true,
        "usage_info": {
            "available_generations": 15,
            "monthly_limit": 20,
            "current_usage": 5,
            "extra_generations": 0,
            "subscription_status": "free",
            "can_upgrade": true,
            "can_purchase_extra": false
        }
    }
    """
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'user_id query parameter is required'
            }), 400
        
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get usage status
        usage_status = UsageTrackingService.check_pose_generation_limit(user)
        
        return jsonify({
            'success': True,
            'usage_info': {
                'available_generations': usage_status.get('available_generations', 0),
                'monthly_limit': usage_status.get('monthly_limit', 0),
                'current_usage': usage_status.get('current_usage', 0),
                'extra_generations': usage_status.get('extra_generations', 0),
                'subscription_status': usage_status.get('subscription_status', 'free'),
                'can_upgrade': user.needs_upgrade_for_poses(),
                'can_purchase_extra': user.can_purchase_extra_generations(),
                'reset_date': user.pose_generations_reset_date.isoformat() if user.pose_generations_reset_date else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@purchase_bp.route('/success', methods=['GET'])
def payment_success():
    """Handle successful payment redirect from Stripe.
    
    Query params:
    - session_id: Stripe checkout session ID
    
    Returns:
    {
        "success": true,
        "message": "Payment successful",
        "subscription_status": "basic",
        "redirect_url": "/dashboard"
    }
    """
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'Missing session_id parameter',
                'redirect_url': '/dashboard'
            }), 400
        
        print(f"[DEBUG] Processing success redirect for session: {session_id}")
        
        # Retrieve the checkout session from Stripe
        from ..config.stripe_config import _ensure_stripe_initialized, retrieve_checkout_session
        _ensure_stripe_initialized()
        
        session = retrieve_checkout_session(session_id)
        if not session:
            return jsonify({
                'success': False,
                'error': 'Invalid session ID',
                'redirect_url': '/dashboard'
            }), 400
        
        print(f"[DEBUG] Retrieved session: {session.id}, status: {session.payment_status}")
        
        # Check if payment was successful
        if session.payment_status != 'paid':
            return jsonify({
                'success': False,
                'error': 'Payment not completed',
                'redirect_url': '/dashboard'
            }), 400
        
        # Get metadata from session
        metadata = session.metadata or {}
        user_id = metadata.get('user_id')
        purchase_type = metadata.get('type')
        plan = metadata.get('plan')
        
        print(f"[DEBUG] Session metadata - user_id: {user_id}, type: {purchase_type}, plan: {plan}")
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Missing user information',
                'redirect_url': '/dashboard'
            }), 400
        
        # Find the user
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'redirect_url': '/dashboard'
            }), 404
        
        print(f"[DEBUG] Found user: {user.email}")
        
        # Process the upgrade based on purchase type
        if purchase_type == 'subscription' and plan:
            # Ensure user is upgraded (in case webhook failed)
            if user.subscription_status != plan:
                print(f"[DEBUG] Upgrading user from {user.subscription_status} to {plan}")
                user.upgrade_to_subscription(plan, session.subscription if hasattr(session, 'subscription') else None)
            else:
                print(f"[DEBUG] User already has {plan} subscription")
            
            return jsonify({
                'success': True,
                'message': f'Successfully upgraded to {plan.title()} subscription!',
                'subscription_status': plan,
                'user_email': user.email,
                'redirect_url': '/dashboard/pose-enhancer'
            })
        
        elif purchase_type == 'recharge':
            generation_count = int(metadata.get('generation_count', 0))
            if generation_count > 0:
                # Add the extra generations to the user's account (in case webhook failed)
                current_extra = user.extra_pose_generations
                user.add_extra_pose_generations(generation_count)
                print(f"[DEBUG] Added {generation_count} extra generations to user {user.email} (was {current_extra}, now {user.extra_pose_generations})")
            
            return jsonify({
                'success': True,
                'message': f'Successfully purchased {generation_count} additional generations!',
                'subscription_status': user.subscription_status,
                'user_email': user.email,
                'redirect_url': '/dashboard/pose-enhancer'
            })
        
        else:
            return jsonify({
                'success': True,
                'message': 'Payment processed successfully!',
                'subscription_status': user.subscription_status,
                'user_email': user.email,
                'redirect_url': '/dashboard'
            })
        
    except Exception as e:
        print(f"Error processing payment success: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}',
            'redirect_url': '/dashboard'
        }), 500


@purchase_bp.route('/customer-portal', methods=['POST'])
def create_customer_portal_session():
    """Create a Stripe customer portal session for subscription management.
    
    Request body:
    {
        "user_id": "user-id-here",
        "return_url": "https://yourapp.com/billing"  // Optional
    }
    
    Returns:
    {
        "success": true,
        "portal_url": "https://billing.stripe.com/session/..."
    }
    """
    try:
        from ..config.stripe_config import _ensure_stripe_initialized
        _ensure_stripe_initialized()
        
        data = request.get_json(force=True, silent=True)
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        # Get user
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'user_id is required'
            }), 400
        
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Check if user has a Stripe customer ID
        if not user.stripe_customer_id:
            return jsonify({
                'success': False,
                'error': 'No Stripe customer found for this user'
            }), 400
        
        # Create customer portal session
        return_url = data.get('return_url', 'http://localhost:3000/dashboard/billing')
        
        portal_session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=return_url,
        )
        
        return jsonify({
            'success': True,
            'portal_url': portal_session.url
        })
        
    except stripe.error.StripeError as e:
        return jsonify({
            'success': False,
            'error': f'Stripe error: {str(e)}'
        }), 400
        
    except Exception as e:
        print(f"Error creating customer portal session: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@purchase_bp.route('/webhook/test', methods=['GET', 'POST'])
def webhook_test():
    """Test webhook endpoint configuration."""
    print(f"[WEBHOOK TEST] Received {request.method} request")
    
    # Check environment variables
    stripe_key = os.getenv('STRIPE_SECRET_KEY')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    config_status = {
        'stripe_secret_key_configured': bool(stripe_key and stripe_key != 'sk_test_your_stripe_secret_key_here'),
        'webhook_secret_configured': bool(webhook_secret),
        'stripe_key_preview': stripe_key[:10] if stripe_key else None,
        'webhook_secret_preview': webhook_secret[:10] if webhook_secret else None
    }
    
    # Test Stripe initialization
    try:
        from ..config.stripe_config import _ensure_stripe_initialized
        _ensure_stripe_initialized()
        config_status['stripe_initialization'] = 'success'
    except Exception as e:
        config_status['stripe_initialization'] = f'failed: {str(e)}'
    
    if request.method == 'POST':
        # Test webhook payload processing
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get('Stripe-Signature')
        
        config_status.update({
            'payload_received': bool(payload),
            'payload_length': len(payload) if payload else 0,
            'signature_header_present': bool(sig_header),
            'content_type': request.headers.get('Content-Type')
        })
    
    return jsonify({
        'success': True,
        'message': 'Webhook test endpoint',
        'method': request.method,
        'configuration': config_status
    })


@purchase_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@purchase_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        'success': False,
        'error': 'Method not allowed'
    }), 405
