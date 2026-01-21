"""
Flask extensions initialization.
"""
import os
import logging
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from app.services.mongodb_service import MongoDBService
from app.services.firebase_service import FirebaseService
from app.services.db_repository import DatabaseRepository
import firebase_admin
from firebase_admin import credentials, auth

# Initialize extensions
jwt = JWTManager()
bcrypt = Bcrypt()

# Initialize Limiter
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
limiter = Limiter(key_func=get_remote_address)

# Global DB instance
db: DatabaseRepository = None
# Keep legacy service for backward compatibility during migration
mongodb_service = MongoDBService()


def get_db() -> DatabaseRepository:
    """Get the active database repository."""
    global db
    if db is None:
        # Default to mongodb if not set
        db = mongodb_service
    return db


def init_extensions(app):
    """Initialize Flask extensions with app instance.
    
    Args:
        app: Flask application instance
    """
    global db
    
    # Initialize extensions
    jwt.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)
    
    # Initialize Firebase Admin (Always needed for Auth if we use Firebase Auth, 
    # but here we also use it for Firestore)
    try:
        if not firebase_admin._apps:
            # Use default credentials (GOOGLE_APPLICATION_CREDENTIALS env var)
            # or try to find a service account file
            cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
            
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                app.logger.info(f"Firebase Admin initialized with credentials from {cred_path}")
            else:
                # Fallback to default (useful for cloud deployment or if env var is set)
                try:
                    firebase_admin.initialize_app()
                    app.logger.info("Firebase Admin initialized with default credentials")
                except Exception as e:
                    app.logger.warning(f"Could not initialize Firebase Admin with default credentials: {e}")
                    pass
    except Exception as e:
        app.logger.error(f"Failed to initialize Firebase Admin: {e}")
    
    # Determine DB Type
    db_type = os.getenv('DB_TYPE', 'mongodb').lower()
    app.logger.info(f"Initializing database: {db_type}")
    
    with app.app_context():
        try:
            if db_type == 'firebase':
                db = FirebaseService()
                db.connect()
                app.logger.info("Firebase (Firestore) service initialized")
            else:
                # Default to MongoDB
                db = mongodb_service
                db.connect()
                app.logger.info("MongoDB service initialized")
            
            # Initialize models and create indexes (if applicable)
            # Note: For Firebase, create_index logs a warning but doesn't fail.
            from app.models.user_mongo import User
            from app.models.character import Character
            from app.models.scene import Scene
            from app.models.scene_memory import (
                SceneMemory, Pose, CharacterState, 
                EnvironmentState, PlotThread
            )
            
            # Initialize indexes for all models
            # This works for both because Repository interface has create_index
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

            app.logger.info(f"Database ({db_type}) and models initialized successfully")
        except Exception as e:
            app.logger.error(f"Failed to initialize Database: {e}")
            raise