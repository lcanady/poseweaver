from app import create_app
from dotenv import load_dotenv
import os

# Load environment variables from the backend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

# Get port from environment (for DigitalOcean App Platform)
port = int(os.getenv('PORT', 5001))
flask_env = os.getenv('FLASK_ENV', 'development')
debug_mode = flask_env == 'development'

print(f"Loading .env from: {env_path}")
print(f"MONGODB_URI configured: {'Yes' if os.getenv('MONGODB_URI') else 'No'}")
print(f"Running on port: {port}")
print(f"Environment: {flask_env}")
print(f"Debug mode: {debug_mode}")

app = create_app()

if __name__ == '__main__':
    # Use SocketIO run method for WebSocket support
    # For production, use eventlet as the async mode
    if flask_env == 'production':
        # Production mode with eventlet
        app.socketio.run(app, 
                        debug=debug_mode, 
                        host='0.0.0.0', 
                        port=port,
                        allow_unsafe_werkzeug=True)  # Allow for production deployment
    else:
        # Development mode
        app.socketio.run(app, debug=debug_mode, host='0.0.0.0', port=port, allow_unsafe_werkzeug=debug_mode) 