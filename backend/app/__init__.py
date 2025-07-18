from flask import Flask
from flask_cors import CORS
import os
from app.extensions import init_extensions
from app.utils.json_encoder import MongoJSONEncoder


def create_app(config_name='development'):
    """Application factory pattern for Flask app creation"""
    app = Flask(__name__)
    
    # Use custom JSON encoder for MongoDB ObjectId serialization
    app.json_encoder = MongoJSONEncoder
    
    # Load configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    
    # JWT configuration
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 43200  # 12 hours
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000  # 30 days
    
    # MongoDB configuration
    app.config['MONGODB_URI'] = os.getenv(
        'MONGODB_URI', 'mongodb://admin:password@localhost:27017/mush_pose_editor?authSource=admin'
    )
    app.config['MONGODB_DB'] = os.getenv('MONGODB_DB', 'mush_pose_editor')
    
    # Legacy SQLAlchemy configuration (kept for compatibility)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 'sqlite:///mush_pose_editor.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    

    
    # Configure CORS for frontend communication with JWT support
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173", 
                       "http://localhost:*", "http://127.0.0.1:*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", 
                           "Access-Control-Allow-Origin", "Origin"],
            "supports_credentials": True,
            "allow_credentials": True
        }
    })
    
    # Initialize extensions
    init_extensions(app)
    
    # Testing configuration
    if config_name == 'testing':
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['MONGODB_URI'] = 'mongodb://admin:password@localhost:27017/test_db?authSource=admin'
        app.config['MONGODB_DB'] = 'test_db'
    else:
        app.config['VENICE_API_KEY'] = os.getenv('VENICE_API_KEY')
        app.config['FLASK_ENV'] = os.getenv('FLASK_ENV', 'development')
    
    # Register blueprints
    from app.api.characters import characters_bp
    from app.api.context import context_bp
    from app.api.pose import pose_bp
    from app.api.models import models_bp
    from app.api.scene_flow import scene_flow_bp
    from app.api.mush_parser import mush_parser_bp
    from app.api.auth import auth_bp
    from app.api.scenes import scenes_bp
    from app.api.character_mgmt import character_mgmt_bp
    from app.api.uploads import uploads_bp, ensure_upload_dir
    
    app.register_blueprint(characters_bp, url_prefix='/api/characters')
    app.register_blueprint(context_bp, url_prefix='/api/context')
    app.register_blueprint(pose_bp, url_prefix='/api/pose')
    app.register_blueprint(models_bp, url_prefix='/api/models')
    app.register_blueprint(scene_flow_bp)
    app.register_blueprint(mush_parser_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(scenes_bp, url_prefix='/api/scenes')
    app.register_blueprint(character_mgmt_bp, url_prefix='/api/characters/mgmt')
    app.register_blueprint(uploads_bp, url_prefix='/api/uploads')
    
    # Ensure upload directories exist at startup
    ensure_upload_dir()
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'mush-pose-editor'}, 200
    
    # Create database tables
    with app.app_context():
        from app.extensions import db
        db.create_all()
    
    return app 