import pytest
from unittest.mock import MagicMock, patch
from app.services.character_creation_service import CharacterCreationService
from app.services.ai_client import AIClient

@pytest.fixture
def mock_ai_client():
    client = MagicMock(spec=AIClient)
    client.generate_completion.return_value = "This is an AI response."
    client.extract_structured_data.return_value = {
        "name": "Jax",
        "description": "Cyber-Noir Detective",
        "background": "Ex-cop in a dark city.",
        "personality": "Cynical but just.",
        "appearance": "Cybernetic eye, trench coat.",
        "traits": ["Cynical", "Just"],
        "speaking_style": "Noir-style metaphors."
    }
    return client

@pytest.fixture
def creation_service(mock_ai_client):
    return CharacterCreationService(mock_ai_client)

def test_start_session(creation_service):
    user_id = "user123"
    session_id = creation_service.start_session(user_id)
    
    assert session_id is not None
    assert session_id in creation_service.sessions
    assert creation_service.sessions[session_id]["user_id"] == user_id
    assert len(creation_service.sessions[session_id]["messages"]) == 1
    assert creation_service.sessions[session_id]["messages"][0]["role"] == "system"

def test_get_ai_response(creation_service, mock_ai_client):
    user_id = "user123"
    session_id = creation_service.start_session(user_id)
    
    response = creation_service.get_ai_response(session_id, "I want to create a detective.")
    
    assert response == "This is an AI response."
    assert len(creation_service.sessions[session_id]["messages"]) == 3 # system, user, assistant
    assert creation_service.sessions[session_id]["messages"][1]["content"] == "I want to create a detective."
    assert creation_service.sessions[session_id]["messages"][2]["content"] == "This is an AI response."

def test_finalize_character(creation_service, mock_ai_client):
    user_id = "user123"
    session_id = creation_service.start_session(user_id)
    creation_service.get_ai_response(session_id, "I want to create a detective.")
    
    extracted_data = creation_service.finalize_character(session_id)
    
    assert extracted_data["name"] == "Jax"
    assert extracted_data["description"] == "Cyber-Noir Detective"
    mock_ai_client.extract_structured_data.assert_called_once()
