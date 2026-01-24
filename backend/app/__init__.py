from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import os
from app.extensions import init_extensions
from app.utils.json_encoder import MongoJSONEncoder


def create_app(config_name='development'):
    """Application factory pattern for Flask app creation"""
    app = Flask(__name__)
    
    # Use custom JSON encoder for MongoDB ObjectId serialization
    app.json_encoder = MongoJSONEncoder

    # Configure Logging
    import logging.config
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                'format': '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(module)s"}',
                'datefmt': '%Y-%m-%dT%H:%M:%SZ'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'json',
                'stream': 'ext://sys.stdout'
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console']
        }
    })
    
    # Load configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    
    # JWT configuration
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 43200  # 12 hours
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000  # 30 days
    
    # Session Configuration
    import redis
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    
    redis_url = os.getenv('REDIS_URL')
    if not redis_url:
        if config_name == 'production':
             raise ValueError("REDIS_URL environment variable is required in production")
        # Fallback for dev/test if needed, or just warn
        app.logger.warning("REDIS_URL not set, session might not work as expected")
        # For dev, maybe we default to localhost if not set, or let it fail? 
        # Requirement said fail loudly in production. 
        # Let's set a default for dev:
        redis_url = 'redis://localhost:6379'
        
    app.config['SESSION_REDIS'] = redis.from_url(redis_url)
    
    # MongoDB configuration
    app.config['MONGODB_URI'] = os.getenv(
        'MONGODB_URI', 'mongodb://admin:password@localhost:27017/mush_pose_editor?authSource=admin'
    )
    app.config['MONGODB_DB'] = os.getenv('MONGODB_DB', 'mush_pose_editor')
    
    # File upload configuration
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    

    
    # Configure CORS for frontend communication with JWT support
    # Specify allowed origins for credentials support
    allowed_origins = [
        "http://localhost:3000",  # Frontend dev server
        "http://localhost:3001",  # Frontend dev server (alt)
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://192.168.12.123:3000",  # Network access
        "https://www.poseweaver.com",  # Production frontend
        "https://poseweaver.com",  # Production frontend (without www)
    ]
    
    # Add additional frontend URL if specified in environment
    frontend_url = os.getenv('FRONTEND_URL')
    if frontend_url and frontend_url not in allowed_origins:
        allowed_origins.append(frontend_url)
    
    CORS(app, 
         origins=allowed_origins,  # Specific origins required for credentials
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-Requested-With", 
                       "Access-Control-Allow-Origin", "Origin"],
         supports_credentials=True)  # Enable credentials support
    
    # Initialize extensions
    init_extensions(app)
    
    # Testing configuration
    if config_name == 'testing':
        app.config['TESTING'] = True
        app.config['MONGODB_URI'] = 'mongodb://admin:password@localhost:27017/test_db?authSource=admin'
        app.config['MONGODB_DB'] = 'test_db'
    else:
        app.config['OPENROUTER_API_KEY'] = os.getenv('OPENROUTER_API_KEY')
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
    from app.api.ai_chat import ai_chat_bp

    from app.api.character_plot_tracking import character_plot_bp
    from app.api.search_summary import search_summary_bp
    from app.api.purchase import purchase_bp
    from app.api.description import description_bp
    from app.api.admin import admin_bp
    from app.api.setup import setup_bp
    from app.api.user import user_bp
    from app.api.notifications import notifications_bp
    from app.api.marketplace import marketplace_bp
    
    app.register_blueprint(characters_bp, url_prefix='/api/characters')
    app.register_blueprint(context_bp, url_prefix='/api/context')
    app.register_blueprint(pose_bp, url_prefix='/api/pose')
    app.register_blueprint(models_bp, url_prefix='/api/models')
    app.register_blueprint(scene_flow_bp)
    app.register_blueprint(mush_parser_bp, url_prefix='/api/mush')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(scenes_bp, url_prefix='/api/scenes')
    app.register_blueprint(character_mgmt_bp, url_prefix='/api/characters/mgmt')
    app.register_blueprint(uploads_bp, url_prefix='/api/uploads')
    app.register_blueprint(ai_chat_bp, url_prefix='/api/characters/ai-chat')

    app.register_blueprint(character_plot_bp, url_prefix='/api/character-plot')
    app.register_blueprint(search_summary_bp, url_prefix='/api/search-summary')
    app.register_blueprint(purchase_bp, url_prefix='/api/purchase')
    app.register_blueprint(description_bp, url_prefix='/api/description')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(setup_bp, url_prefix='/api/setup')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(notifications_bp, url_prefix='/api')
    app.register_blueprint(marketplace_bp, url_prefix='/api/marketplace')
    
    # Ensure upload directories exist at startup
    ensure_upload_dir()
    
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'service': 'poseweaver-backend'}, 200
    
    # Initialize MongoDB indexes
    with app.app_context():
        # MongoDB indexes are initialized in init_extensions
        pass
    
    # Initialize SocketIO for WebSocket support
    socketio = SocketIO(
        app,
        cors_allowed_origins=allowed_origins,
        async_mode='threading',
        logger=True,
        engineio_logger=True,
        max_http_buffer_size=10 * 1024 * 1024  # 10MB
    )
    
    # Initialize WebSocket service
    from app.services.websocket_service import WebSocketService
    websocket_service = WebSocketService(socketio)
    
    # Store socketio instance on app for access in other modules
    app.socketio = socketio
    
    return app 