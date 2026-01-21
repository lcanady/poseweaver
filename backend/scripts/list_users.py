
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH')

def list_users():
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    
    users = list(db.collection('users').stream())
    print(f"Found {len(users)} users in Firestore:")
    for user in users:
        data = user.to_dict()
        print(f"ID: {user.id}, Email: {data.get('email')}, Admin: {data.get('is_admin')}, Sub: {data.get('subscription_status')}")

if __name__ == "__main__":
    list_users()
