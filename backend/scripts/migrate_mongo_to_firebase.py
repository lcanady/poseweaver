"""
Migration script to move data from MongoDB to Firebase Firestore.
"""
import os
import sys
import logging
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://admin:password@localhost:27017/mush_pose_editor?authSource=admin')
MONGODB_DB_NAME = os.getenv('MONGODB_DB', 'mush_pose_editor')
FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH')

def setup_connections():
    """Setup connections to MongoDB and Firestore."""
    # Connect to MongoDB
    try:
        mongo_client = MongoClient(MONGODB_URI)
        mongo_db = mongo_client[MONGODB_DB_NAME]
        logger.info(f"Connected to MongoDB: {MONGODB_DB_NAME}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        sys.exit(1)

    # Connect to Firestore
    try:
        if not firebase_admin._apps:
            if FIREBASE_CREDENTIALS_PATH and os.path.exists(FIREBASE_CREDENTIALS_PATH):
                cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
            else:
                firebase_admin.initialize_app()
        
        firestore_db = firestore.client()
        logger.info("Connected to Firestore")
    except Exception as e:
        logger.error(f"Failed to connect to Firestore: {e}")
        sys.exit(1)
        
    return mongo_db, firestore_db

def convert_object_id(doc):
    """Convert ObjectId to string and remap _id to id."""
    if not doc:
        return doc
        
    new_doc = doc.copy()
    
    # Handle _id
    if '_id' in new_doc:
        new_doc['id'] = str(new_doc['_id'])
        del new_doc['_id']
        
    # Recursive conversion for nested dicts and lists
    for key, value in new_doc.items():
        if isinstance(value, ObjectId):
            new_doc[key] = str(value)
        elif isinstance(value, dict):
            new_doc[key] = convert_object_id(value)
        elif isinstance(value, list):
            new_list = []
            for item in value:
                if isinstance(item, ObjectId):
                    new_list.append(str(item))
                elif isinstance(item, dict):
                    new_list.append(convert_object_id(item))
                else:
                    new_list.append(item)
            new_doc[key] = new_list
            
    return new_doc

def reset_firestore_collection(db, collection_name, batch_size=100):
    """Delete all documents in a Firestore collection."""
    logger.info(f"Clearing collection: {collection_name}")
    collection_ref = db.collection(collection_name)
    docs = collection_ref.limit(batch_size).stream()
    deleted = 0
    
    for doc in docs:
        doc.reference.delete()
        deleted += 1
        
    if deleted >= batch_size:
        return reset_firestore_collection(db, collection_name, batch_size)
    
    logger.info(f"Cleared {deleted} documents from {collection_name}")


def migrate_collection(mongo_db, firestore_db, collection_name, transform_func=None):
    """Migrate a single collection."""
    logger.info(f"Migrating collection: {collection_name}")
    
    try:
        mongo_collection = mongo_db[collection_name]
        count = mongo_collection.count_documents({})
        logger.info(f"Found {count} documents in MongoDB {collection_name}")
        
        cursor = mongo_collection.find({})
        migrated = 0
        
        batch = firestore_db.batch()
        batch_count = 0
        MAX_BATCH_SIZE = 400  # Firestore limit is 500
        
        for doc in cursor:
            # Basic conversion
            new_doc = convert_object_id(doc)
            
            # Apply specific transformation if provided
            if transform_func:
                new_doc = transform_func(new_doc)
            
            # Add to batch
            doc_ref = firestore_db.collection(collection_name).document(new_doc['id'])
            batch.set(doc_ref, new_doc)
            batch_count += 1
            migrated += 1
            
            if batch_count >= MAX_BATCH_SIZE:
                batch.commit()
                batch = firestore_db.batch()
                batch_count = 0
                logger.info(f"Migrated {migrated}/{count} documents...")
        
        # Commit remaining
        if batch_count > 0:
            batch.commit()
            
        logger.info(f"Successfully migrated {migrated} documents to {collection_name}")
        
    except Exception as e:
        logger.error(f"Error migrating {collection_name}: {e}")

def transform_scene(doc):
    """Transform scene document for Firestore."""
    # Populate participant_ids if missing
    if 'participants' in doc and 'participant_ids' not in doc:
        if isinstance(doc['participants'], dict):
            doc['participant_ids'] = list(doc['participants'].keys())
        elif isinstance(doc['participants'], list):
            # If stored as list (legacy?), extract IDs if possible
            doc['participant_ids'] = []
            
    return doc

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Migrate data from MongoDB to Firestore.')
    parser.parse_args()

    logger.info("Starting migration from MongoDB to Firestore...")
    
    mongo_db, firestore_db = setup_connections()
    
    # Optional: Clear existing Firestore data?
    # reset_firestore_collection(firestore_db, 'users')
    # reset_firestore_collection(firestore_db, 'characters')
    # reset_firestore_collection(firestore_db, 'scenes')
    # reset_firestore_collection(firestore_db, 'scene_memory')
    # reset_firestore_collection(firestore_db, 'poses')
    
    # Migrate Collections
    migrate_collection(mongo_db, firestore_db, 'users')
    migrate_collection(mongo_db, firestore_db, 'characters')
    migrate_collection(mongo_db, firestore_db, 'scenes', transform_func=transform_scene)
    migrate_collection(mongo_db, firestore_db, 'scene_memory')
    # Migrate Poses if they are in their own collection (Scene Memory model suggests 'poses' collection)
    migrate_collection(mongo_db, firestore_db, 'poses')
    migrate_collection(mongo_db, firestore_db, 'character_states')
    migrate_collection(mongo_db, firestore_db, 'environment_states')
    migrate_collection(mongo_db, firestore_db, 'plot_threads')
    
    logger.info("Migration completed successfully!")

if __name__ == "__main__":
    main()
