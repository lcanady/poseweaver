import pytest
import os
from app import create_app


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Set testing environment
    os.environ['VENICE_API_KEY'] = 'test_key_12345'
    
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'VENICE_API_KEY': 'test_key_12345',
    })
    
    yield app


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test runner for the Flask application's Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def mock_venice_response():
    """Mock response for Venice.ai API calls."""
    return {
        "choices": [
            {
                "message": {
                    "content": "Mock AI response for testing purposes."
                }
            }
        ]
    }


@pytest.fixture
def sample_character_data():
    """Sample character data for testing."""
    return {
        "background": "Former noble turned mercenary",
        "personality": ["bitter", "aristocratic", "prideful"],
        "skills": ["swordsmanship", "etiquette", "leadership"],
        "motivations": ["restore honor", "seek redemption"],
        "relationships": [],
        "physical_description": "Tall, well-built, noble bearing",
        "psychological_traits": ["trust issues", "perfectionist"]
    }


@pytest.fixture
def sample_pose_context():
    """Sample pose context data for testing."""
    return {
        "actions": ["draws sword", "steps forward"],
        "emotions": ["determined", "cautious"],
        "environmental_details": ["tavern", "dim lighting", "crowded"],
        "character_interactions": ["direct confrontation"],
        "response_hooks": ["challenge issued", "waiting for response"]
    } 