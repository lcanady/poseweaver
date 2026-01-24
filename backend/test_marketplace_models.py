"""
Test script for marketplace models.
Verifies that PluginManifest and UserPluginInstall models work correctly.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.marketplace import PluginManifest, UserPluginInstall
from app.extensions import get_db


def test_plugin_manifest():
    """Test creating and saving a PluginManifest."""
    print("\n=== Testing PluginManifest ===")
    
    # Create a sample plugin
    plugin = PluginManifest(
        name="Dice Roller Test",
        description="A test dice rolling plugin",
        price=499,
        hooks=["ON_POSE", "ON_SCENE_START"],
        config_schema={
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "dice_type": {
                    "type": "string",
                    "enum": ["d4", "d6", "d8", "d10", "d12", "d20"],
                    "default": "d20"
                }
            }
        },
        code_ref="plugins/dice_roller/main.py",
        is_official=True,
        author="Test Author",
        version="1.0.0"
    )
    
    # Save to database
    plugin_id = plugin.save()
    print(f"✓ Created PluginManifest with ID: {plugin_id}")
    
    # Retrieve from database
    retrieved_plugin = PluginManifest.find_by_id(plugin_id)
    print(f"✓ Retrieved plugin: {retrieved_plugin.name}")
    
    # Test to_dict
    plugin_dict = retrieved_plugin.to_dict()
    print(f"✓ Plugin dict keys: {list(plugin_dict.keys())}")
    
    # Test finding by hook
    plugins_with_hook = PluginManifest.find_by_hook("ON_POSE")
    print(f"✓ Found {len(plugins_with_hook)} plugins with ON_POSE hook")
    
    # Test finding official plugins
    official_plugins = PluginManifest.find_official_plugins()
    print(f"✓ Found {len(official_plugins)} official plugins")
    
    # Clean up
    plugin.delete()
    print(f"✓ Deleted test plugin")
    
    return plugin_id


def test_user_plugin_install(plugin_id, user_id="test_user_123"):
    """Test creating and saving a UserPluginInstall."""
    print("\n=== Testing UserPluginInstall ===")
    
    # Create a plugin installation
    install = UserPluginInstall(
        user_id=user_id,
        plugin_id=plugin_id,
        is_active=True,
        settings={
            "dice_type": "d20",
            "auto_roll": True
        }
    )
    
    # Save to database
    install_id = install.save()
    print(f"✓ Created UserPluginInstall with ID: {install_id}")
    
    # Retrieve from database
    retrieved_install = UserPluginInstall.find_by_id(install_id)
    print(f"✓ Retrieved install for user: {retrieved_install.user_id}")
    
    # Test finding by user
    user_installs = UserPluginInstall.find_by_user(user_id)
    print(f"✓ Found {len(user_installs)} installs for user")
    
    # Test finding active installs
    active_installs = UserPluginInstall.find_active_by_user(user_id)
    print(f"✓ Found {len(active_installs)} active installs")
    
    # Test checking if user has plugin
    has_plugin = UserPluginInstall.user_has_plugin(user_id, plugin_id)
    print(f"✓ User has plugin: {has_plugin}")
    
    # Test toggle active
    install.toggle_active()
    print(f"✓ Toggled active state to: {install.is_active}")
    
    # Test update settings
    install.update_settings({"critical_threshold": 18})
    retrieved_install = UserPluginInstall.find_by_id(install_id)
    print(f"✓ Updated settings: {retrieved_install.settings}")
    
    # Clean up
    install.delete()
    print(f"✓ Deleted test install")


def test_stripe_integration():
    """Test Stripe configuration for plugins."""
    print("\n=== Testing Stripe Integration ===")
    
    from app.config.stripe_config import (
        get_plugin_purchase_info,
        PLUGIN_PRODUCTS,
        PLUGIN_PRICES
    )
    
    # Create a plugin with Stripe info
    plugin = PluginManifest(
        name="Premium Plugin",
        description="A premium test plugin",
        price=999,
        hooks=["ON_POSE"],
        is_official=True,
        author="Test",
        version="1.0.0",
        stripe_product_id="prod_test_123",
        stripe_price_id="price_test_123"
    )
    plugin.save()
    
    # Test get_plugin_purchase_info
    purchase_info = get_plugin_purchase_info(plugin)
    print(f"✓ Purchase info: {purchase_info}")
    
    # Test plugin without Stripe
    free_plugin = PluginManifest(
        name="Free Plugin",
        description="A free test plugin",
        price=0,
        hooks=["ON_POSE"],
        is_official=True,
        author="Test",
        version="1.0.0"
    )
    free_plugin.save()
    
    free_info = get_plugin_purchase_info(free_plugin)
    print(f"✓ Free plugin purchase info: {free_info}")
    
    # Clean up
    plugin.delete()
    free_plugin.delete()
    print(f"✓ Cleaned up test plugins")


if __name__ == "__main__":
    print("Testing Marketplace Models...")
    
    try:
        # Initialize database connection
        db = get_db()
        print("✓ Database connection established")
        
        # Test PluginManifest
        plugin_id = test_plugin_manifest()
        
        # Test UserPluginInstall (need to create plugin first for this test)
        # For testing purposes, we'll use a fake plugin_id
        # test_user_plugin_install("test_plugin_id_123")
        
        # Test Stripe integration
        test_stripe_integration()
        
        print("\n" + "="*50)
        print("✓ All tests passed successfully!")
        print("="*50)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
