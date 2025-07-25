from app import create_app
from dotenv import load_dotenv
import os

# Load environment variables from the backend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

print(f"Loading .env from: {env_path}")
print(f"MONGODB_URI configured: {'Yes' if os.getenv('MONGODB_URI') else 'No'}")

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 