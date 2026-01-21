
import os
import sys
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_client import AIClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Test connection to AI provider"""
    logger.info("Initializing AI Client...")
    
    # Load env vars if managing manually or assume already set
    # For this script we rely on the environment being set or default handling in AIClient
    
    client = AIClient() # Should pick up from OS env
    
    logger.info(f"Using Base URL: {client.base_url}")
    logger.info(f"Using Model: {client.model}")
    
    try:
        logger.info("Sending test request...")
        response = client.generate_completion(
            prompt="Hello! Are you working?",
            model=client.model, # Use configured model
            max_tokens=50
        )
        logger.info("\nSUCCESS! Response received:")
        logger.info("-" * 40)
        logger.info(response)
        logger.info("-" * 40)
        return True
    except Exception as e:
        logger.error(f"\nFAILURE: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
