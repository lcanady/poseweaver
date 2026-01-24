"""
Marketplace API endpoints for plugin browsing, installation, and configuration.
"""
from flask import Blueprint, request, jsonify
from ..middleware.auth_middleware import require_auth
from ..models.marketplace import PluginManifest, UserPluginInstall
from datetime import datetime, UTC

marketplace_bp = Blueprint('marketplace', __name__)


@marketplace_bp.route('/plugins', methods=['GET'])
@require_auth
def list_plugins():
    """List all available plugins with filtering options.
    
    Query parameters:
    - owned (boolean): Filter by user's owned plugins
    - official (boolean): Filter by official plugins only
    - hook (string): Filter by plugins supporting specific hook
    
    Returns:
    {
        "success": true,
        "plugins": [
            {
                "id": "uuid",
                "name": "Dice Roller",
                "description": "...",
                "price": 0,
                "version": "1.0.0",
                "hooks": ["ON_POSE_CREATE"],
                "is_official": true,
                "author": "PoseWeaver",
                "rating": 4.5,
                "download_count": 100,
                "is_installed": false
            }
        ]
    }
    """
    try:
        current_user = request.current_user
        
        if not current_user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get query parameters
        owned = request.args.get('owned', '').lower() == 'true'
        official = request.args.get('official', '').lower() == 'true'
        hook = request.args.get('hook')
        
        # Build plugin list based on filters
        if hook:
            plugins = PluginManifest.find_by_hook(hook)
        elif official:
            plugins = PluginManifest.find_official_plugins()
        else:
            plugins = PluginManifest.find_all()
        
        # Get user's installed plugins
        user_installs = UserPluginInstall.find_by_user(current_user.id)
        installed_plugin_ids = {install.plugin_id for install in user_installs}
        
        # Format plugin data
        plugin_list = []
        for plugin in plugins:
            plugin_data = plugin.to_dict()
            plugin_data['is_installed'] = plugin.id in installed_plugin_ids
            
            # If filtering by owned, only include installed plugins
            if owned and not plugin_data['is_installed']:
                continue
                
            plugin_list.append(plugin_data)
        
        return jsonify({
            'success': True,
            'plugins': plugin_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve plugins: {str(e)}'
        }), 500


@marketplace_bp.route('/install/<plugin_id>', methods=['POST'])
@require_auth
def install_plugin(plugin_id):
    """Install or purchase a plugin.
    
    For free plugins: Immediately creates UserPluginInstall record
    For paid plugins: Mock purchase (returns success, creates install record)
    
    Returns:
    {
        "success": true,
        "message": "Plugin installed successfully",
        "install": {
            "install_id": "uuid",
            "plugin_id": "uuid",
            "is_active": true,
            "settings": {},
            "purchased_at": "2026-01-21T15:00:00Z"
        }
    }
    """
    try:
        current_user = request.current_user
        
        if not current_user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Find the plugin
        plugin = PluginManifest.find_by_id(plugin_id)
        if not plugin:
            return jsonify({
                'success': False,
                'error': 'Plugin not found'
            }), 404
        
        # Check if user already owns this plugin
        existing_install = UserPluginInstall.find_by_user_and_plugin(
            current_user.id, 
            plugin_id
        )
        
        if existing_install:
            return jsonify({
                'success': False,
                'error': 'Plugin already installed',
                'error_code': 'ALREADY_INSTALLED'
            }), 409
        
        # Mock purchase flow for paid plugins
        if plugin.price > 0:
            # In a real implementation, this would:
            # 1. Create Stripe checkout session
            # 2. Wait for webhook confirmation
            # 3. Create install record after payment
            # For now, we'll mock the purchase
            print(f"[MOCK PURCHASE] User {current_user.id} purchasing plugin {plugin.name} for ${plugin.price/100:.2f}")
        
        # Create installation record
        install = UserPluginInstall(
            user_id=current_user.id,
            plugin_id=plugin_id,
            is_active=True,
            settings={},  # Start with empty settings
            purchased_at=datetime.now(UTC)
        )
        install.save()
        
        # Increment plugin download count
        plugin.increment_download_count()
        
        return jsonify({
            'success': True,
            'message': 'Plugin installed successfully',
            'install': install.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to install plugin: {str(e)}'
        }), 500


@marketplace_bp.route('/config/<install_id>', methods=['PATCH'])
@require_auth
def update_plugin_config(install_id):
    """Update plugin configuration settings.
    
    Request body:
    {
        "settings": {
            "die_type": "d10",
            "auto_roll": true
        }
    }
    
    Returns:
    {
        "success": true,
        "message": "Plugin settings updated successfully",
        "install": {
            "install_id": "uuid",
            "plugin_id": "uuid",
            "is_active": true,
            "settings": {
                "die_type": "d10",
                "auto_roll": true
            },
            "purchased_at": "2026-01-21T15:00:00Z"
        }
    }
    """
    try:
        current_user = request.current_user
        
        if not current_user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get request data
        data = request.get_json()
        if not data or 'settings' not in data:
            return jsonify({
                'success': False,
                'error': 'settings field is required'
            }), 400
        
        new_settings = data['settings']
        if not isinstance(new_settings, dict):
            return jsonify({
                'success': False,
                'error': 'settings must be a JSON object'
            }), 400
        
        # Find the installation
        install = UserPluginInstall.find_by_id(install_id)
        if not install:
            return jsonify({
                'success': False,
                'error': 'Plugin installation not found'
            }), 404
        
        # Verify ownership
        if install.user_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Unauthorized: You do not own this plugin installation'
            }), 403
        
        # Optional: Validate settings against plugin's config_schema
        # For now, we'll do basic validation by checking if plugin exists
        plugin = PluginManifest.find_by_id(install.plugin_id)
        if not plugin:
            return jsonify({
                'success': False,
                'error': 'Associated plugin not found'
            }), 404
        
        # TODO: Add JSON Schema validation against plugin.config_schema
        # For now, we accept any valid JSON object
        
        # Update settings
        install.update_settings(new_settings)
        
        return jsonify({
            'success': True,
            'message': 'Plugin settings updated successfully',
            'install': install.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to update plugin settings: {str(e)}'
        }), 500


@marketplace_bp.route('/installs', methods=['GET'])
@require_auth
def list_user_installs():
    """List all plugin installations for the current user.
    
    Query parameters:
    - active_only (boolean): Only return active plugins
    
    Returns:
    {
        "success": true,
        "installs": [
            {
                "install_id": "uuid",
                "plugin_id": "uuid",
                "plugin_name": "Dice Roller",
                "is_active": true,
                "settings": {},
                "purchased_at": "2026-01-21T15:00:00Z"
            }
        ]
    }
    """
    try:
        current_user = request.current_user
        
        if not current_user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get query parameters
        active_only = request.args.get('active_only', '').lower() == 'true'
        
        # Get user's installations
        if active_only:
            installs = UserPluginInstall.find_active_by_user(current_user.id)
        else:
            installs = UserPluginInstall.find_by_user(current_user.id)
        
        # Enrich with plugin information
        install_list = []
        for install in installs:
            install_data = install.to_dict()
            
            # Get plugin name
            plugin = PluginManifest.find_by_id(install.plugin_id)
            if plugin:
                install_data['plugin_name'] = plugin.name
                install_data['plugin_version'] = plugin.version
            
            install_list.append(install_data)
        
        return jsonify({
            'success': True,
            'installs': install_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve installations: {str(e)}'
        }), 500


@marketplace_bp.route('/toggle/<install_id>', methods=['POST'])
@require_auth
def toggle_plugin(install_id):
    """Toggle a plugin's active state.
    
    Returns:
    {
        "success": true,
        "message": "Plugin activated/deactivated",
        "install": {...}
    }
    """
    try:
        current_user = request.current_user
        
        if not current_user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Find the installation
        install = UserPluginInstall.find_by_id(install_id)
        if not install:
            return jsonify({
                'success': False,
                'error': 'Plugin installation not found'
            }), 404
        
        # Verify ownership
        if install.user_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Unauthorized: You do not own this plugin installation'
            }), 403
        
        # Toggle active state
        install.toggle_active()
        
        status = 'activated' if install.is_active else 'deactivated'
        
        return jsonify({
            'success': True,
            'message': f'Plugin {status} successfully',
            'install': install.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to toggle plugin: {str(e)}'
        }), 500
