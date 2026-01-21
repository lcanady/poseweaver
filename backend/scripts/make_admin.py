
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH')

def make_admin(email):
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    
    users = list(db.collection('users').where('email', '==', email).stream())
    if not users:
        print(f"User {email} not found")
        return

    user = users[0]
    print(f"Updating user {user.id} ({email}) to admin...")
    user.reference.update({'is_admin': True})
    print("Done!")

if __name__ == "__main__":
    make_admin("lem.canady@gmail.com")
