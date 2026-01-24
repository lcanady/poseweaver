"""
Scene invitation API endpoints.
"""
import secrets
from flask import Blueprint, request, jsonify, current_app
from http import HTTPStatus
from datetime import datetime, UTC, timedelta

from app.models.scene_invite import SceneInvite, SceneRole, InviteStatus
from app.services.scene_service import SceneService
from app.middleware.auth_middleware import require_auth, get_current_identity

# Create blueprint
scene_invites_bp = Blueprint('scene_invites', __name__)


@scene_invites_bp.route('/scenes/<scene_id>/invite', methods=['POST'])
@require_auth
def invite_user(scene_id):
    """Invite a user to a scene by email.
    
    Request body:
    {
        "email": "user@example.com",
        "role": "participant",  // owner, co-author, participant, viewer
        "message": "Join my scene!"  // Optional
    }
    """
    current_user = get_current_identity()
    data = request.get_json()
    
    # Validate request
    if not data or 'email' not in data:
        return jsonify({
            'success': False,
            'message': 'Email is required'
        }), HTTPStatus.BAD_REQUEST
    
    try:
        # Verify user has permission to invite (co-author or owner)
        scene = SceneService.get_scene(scene_id, current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        if not scene.can_edit(current_user):
            return jsonify({
                'success': False,
                'message': 'Only scene owners and co-authors can invite users'
            }), HTTPStatus.FORBIDDEN
        
        # Get role (default to participant)
        role = data.get('role', 'participant')
        if role not in [r.value for r in SceneRole]:
            return jsonify({
                'success': False,
                'message': f'Invalid role. Must be one of: {[r.value for r in SceneRole]}'
            }), HTTPStatus.BAD_REQUEST
        
        # Generate unique invite code
        invite_code = secrets.token_urlsafe(16)
        
        # Create invite
        invite = SceneInvite(
            scene_id=scene_id,
            invited_by_user_id=current_user,
            invited_user_email=data['email'],
            role=SceneRole(role),
            invite_code=invite_code,
            message=data.get('message'),
            expires_at=datetime.now(UTC) + timedelta(days=7)
        )
        
        invite_id = invite.save()
        
        # TODO: Send email notification
        
        return jsonify({
            'success': True,
            'data': {
                'invite': invite.to_dict(),
                'invite_link': f'/scenes/invites/{invite_code}'
            }
        }), HTTPStatus.CREATED
        
    except Exception as e:
        current_app.logger.error(f"Error inviting user: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while creating the invitation'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@scene_invites_bp.route('/scenes/<scene_id>/invite-link', methods=['POST'])
@require_auth
def generate_invite_link(scene_id):
    """Generate a shareable invite link.
    
    Request body:
    {
        "role": "participant",
        "expires_in_hours": 48
    }
    """
    current_user = get_current_identity()
    data = request.get_json() or {}
    
    try:
        # Verify permissions
        scene = SceneService.get_scene(scene_id, current_user)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found or access denied'
            }), HTTPStatus.NOT_FOUND
        
        if not scene.can_edit(current_user):
            return jsonify({
                'success': False,
                'message': 'Only scene owners and co-authors can create invite links'
            }), HTTPStatus.FORBIDDEN
        
        # Generate invite code and update scene
        invite_code = secrets.token_urlsafe(16)
        expires_hours = data.get('expires_in_hours', 48)
        
        scene.invite_code = invite_code
        scene.invite_code_expires = datetime.now(UTC) + timedelta(hours=expires_hours)
        scene.save()
        
        return jsonify({
            'success': True,
            'data': {
                'invite_code': invite_code,
                'invite_link': f'/scenes/join/{invite_code}',
                'expires_at': scene.invite_code_expires.isoformat(),
                'role': data.get('role', 'participant')
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating invite link: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while generating the invite link'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@scene_invites_bp.route('/scenes/invites', methods=['GET'])
@require_auth
def list_invites():
    """List pending invitations for the current user."""
    current_user = get_current_identity()
    
    try:
        # Get user email from database
        from app.models.user_mongo import User
        user = User.find_by_id(current_user)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), HTTPStatus.NOT_FOUND
        
        # Find pending invites
        from app.extensions import get_db
        db = get_db()
        
        invites_data = db.find_many(
            SceneInvite.COLLECTION_NAME,
            {
                'invited_user_email': user.email,
                'status': InviteStatus.PENDING.value
            },
            sort=[('created_at', -1)]
        )
        
        invites = [SceneInvite.from_dict(inv) for inv in invites_data if inv]
        
        # Filter out expired invites
        valid_invites = [inv for inv in invites if inv.can_accept()]
        
        return jsonify({
            'success': True,
            'data': [inv.to_dict() for inv in valid_invites]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error listing invites: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving invitations'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@scene_invites_bp.route('/scenes/invites/<invite_code>', methods=['GET'])
def get_invite(invite_code):
    """Get invite details by code (public endpoint)."""
    try:
        from app.extensions import get_db
        db = get_db()
        
        invite_data = db.find_one(
            SceneInvite.COLLECTION_NAME,
            {'invite_code': invite_code}
        )
        
        if not invite_data:
            return jsonify({
                'success': False,
                'message': 'Invitation not found'
            }), HTTPStatus.NOT_FOUND
        
        invite = SceneInvite.from_dict(invite_data)
        
        if invite.is_expired():
            return jsonify({
                'success': False,
                'message': 'This invitation has expired'
            }), HTTPStatus.GONE
        
        if invite.status != InviteStatus.PENDING:
            return jsonify({
                'success': False,
                'message': f'This invitation has already been {invite.status.value}'
            }), HTTPStatus.GONE
        
        # Get scene details
        scene = SceneService.get_scene(invite.scene_id, invite.invited_by_user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'invite': invite.to_dict(),
                'scene': {
                    'id': scene.id,
                    'name': scene.name,
                    'description': scene.description
                } if scene else None
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting invite: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while retrieving the invitation'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@scene_invites_bp.route('/scenes/invites/<invite_code>/accept', methods=['POST'])
@require_auth
def accept_invite(invite_code):
    """Accept a scene invitation."""
    current_user = get_current_identity()
    
    try:
        from app.extensions import get_db
        from app.models.user_mongo import User
        
        db = get_db()
        
        # Get user email
        user = User.find_by_id(current_user)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), HTTPStatus.NOT_FOUND
        
        # Get invite
        invite_data = db.find_one(
            SceneInvite.COLLECTION_NAME,
            {'invite_code': invite_code}
        )
        
        if not invite_data:
            return jsonify({
                'success': False,
                'message': 'Invitation not found'
            }), HTTPStatus.NOT_FOUND
        
        invite = SceneInvite.from_dict(invite_data)
        
        # Verify invite can be accepted
        if not invite.can_accept():
            return jsonify({
                'success': False,
                'message': 'This invitation cannot be accepted (expired or already used)'
            }), HTTPStatus.BAD_REQUEST
        
        # Verify email matches
        if invite.invited_user_email != user.email:
            return jsonify({
                'success': False,
                'message': 'This invitation was sent to a different email address'
            }), HTTPStatus.FORBIDDEN
        
        # Add permission to scene
        scene = SceneService.get_scene(invite.scene_id, invite.invited_by_user_id)
        if not scene:
            return jsonify({
                'success': False,
                'message': 'Scene not found'
            }), HTTPStatus.NOT_FOUND
        
        scene.add_permission(current_user, invite.role.value)
        scene.save()
        
        # Update invite status
        invite.status = InviteStatus.ACCEPTED
        invite.accepted_at = datetime.now(UTC)
        invite.save()
        
        return jsonify({
            'success': True,
            'data': {
                'scene': scene.to_dict(),
                'role': invite.role.value
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error accepting invite: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while accepting the invitation'
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@scene_invites_bp.route('/scenes/invites/<invite_code>/decline', methods=['POST'])
@require_auth
def decline_invite(invite_code):
    """Decline a scene invitation."""
    current_user = get_current_identity()
    
    try:
        from app.extensions import get_db
        from app.models.user_mongo import User
        
        db = get_db()
        user = User.find_by_id(current_user)
        
        invite_data = db.find_one(
            SceneInvite.COLLECTION_NAME,
            {'invite_code': invite_code}
        )
        
        if not invite_data:
            return jsonify({
                'success': False,
                'message': 'Invitation not found'
            }), HTTPStatus.NOT_FOUND
        
        invite = SceneInvite.from_dict(invite_data)
        
        # Verify email matches
        if user and invite.invited_user_email != user.email:
            return jsonify({
                'success': False,
                'message': 'This invitation was sent to a different email address'
            }), HTTPStatus.FORBIDDEN
        
        # Update status
        invite.status = InviteStatus.DECLINED
        invite.save()
        
        return jsonify({
            'success': True,
            'message': 'Invitation declined'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error declining invite: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while declining the invitation'
        }), HTTPStatus.INTERNAL_SERVER_ERROR
