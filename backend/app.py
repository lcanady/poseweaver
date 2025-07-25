from app import create_app
from dotenv import load_dotenv
import os

# Load environment variables
# In production (Heroku), environment variables are set via config vars
# In development, load from .env file
if os.path.exists('.env'):
    load_dotenv()

app = create_app()

if __name__ == '__main__':
    # Use PORT environment variable for Heroku, fallback to 5001 for local development
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port) 