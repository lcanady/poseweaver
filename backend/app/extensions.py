"""
Flask extensions initialization.
"""
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from app.services.mongodb_service import MongoDBService

# Initialize extensions
jwt = JWTManager()
bcrypt = Bcrypt()

# Initialize MongoDB service
mongodb_service = MongoDBService()


def init_extensions(app):
    """Initialize Flask extensions with app instance.
    
    Args:
        app: Flask application instance
    """
    # Initialize extensions
    jwt.init_app(app)
    bcrypt.init_app(app)
    
    # Initialize MongoDB connection
    with app.app_context():
        try:
            mongodb_service.connect()
            
            # Only initialize indexes if MongoDB connection is successful
            if mongodb_service.db is not None:
                # Initialize models and create indexes
                from app.models.user_mongo import User
                from app.models.character import Character
                from app.models.scene import Scene
                from app.models.scene_memory import (
                    SceneMemory, Pose, CharacterState, 
                    EnvironmentState, PlotThread
                )
                
                # Initialize indexes for all models
                User.initialize_indexes()
                Character.initialize_indexes()
                Scene.initialize_indexes()
                
                # Initialize indexes for scene memory models using migration system
                from app.migrations.migration_manager import run_migrations
                migration_success = run_migrations()
                
                if not migration_success:
                    app.logger.warning("Some migrations failed, falling back to individual index initialization")
                    SceneMemory.initialize_indexes()
                    Pose.initialize_indexes()
                    CharacterState.initialize_indexes()
                    EnvironmentState.initialize_indexes()
                    PlotThread.initialize_indexes()
                
                app.logger.info("MongoDB service and models initialized successfully")
            else:
                app.logger.warning("MongoDB connection failed - running in development mode without database")
                
        except Exception as e:
            app.logger.error(f"Failed to initialize MongoDB: {e}")
            app.logger.warning("Continuing without MongoDB - some features may not work")
            # Don't raise the exception, allow the app to continue without MongoDB