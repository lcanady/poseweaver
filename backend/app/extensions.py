"""
Flask extensions initialization.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from app.services.mongodb_service import MongoDBService

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()

# Initialize MongoDB service
mongodb_service = MongoDBService()


def init_extensions(app):
    """Initialize Flask extensions with app instance.
    
    Args:
        app: Flask application instance
    """
    # Initialize SQLAlchemy and other extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    
    # JWT manager already initialized above
    
    # Initialize MongoDB connection
    with app.app_context():
        try:
            mongodb_service.connect()
            
            # Initialize models and create indexes
            from app.models.user_mongo import User
            from app.models.character import Character
            from app.models.scene import Scene
            
            # Initialize indexes for all models
            User.initialize_indexes()
            Character.initialize_indexes()
            Scene.initialize_indexes()
            
            app.logger.info("MongoDB service and models initialized successfully")
        except Exception as e:
            app.logger.error(f"Failed to initialize MongoDB: {e}")
            raise