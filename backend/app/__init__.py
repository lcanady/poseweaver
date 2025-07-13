from flask import Flask
from flask_cors import CORS
import os


def create_app(config_name='development'):
    """Application factory pattern for Flask app creation"""
    app = Flask(__name__)
    
    # Configure CORS for frontend communication
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:5173"],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Load configuration
    if config_name == 'testing':
        app.config['TESTING'] = True
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
    
    app.register_blueprint(characters_bp, url_prefix='/api/characters')
    app.register_blueprint(context_bp, url_prefix='/api/context')
    app.register_blueprint(pose_bp, url_prefix='/api/pose')
    app.register_blueprint(models_bp, url_prefix='/api/models')
    app.register_blueprint(scene_flow_bp)
    app.register_blueprint(mush_parser_bp)
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'mush-pose-editor'}, 200
    
    return app 