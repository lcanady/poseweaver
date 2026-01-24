from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
from bson import ObjectId
from app.services.ai_client import AIClient
from app.services.memory_manager_service import MemoryManagerService
from app.models.character import Character

class CharacterCreationService:
    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client
        self.memory_manager = MemoryManagerService(window_size=6, max_summary_messages=20)
        # In a real app, we'd store these in a database (e.g. MongoDB collection 'creation_sessions')
        # For now, we'll assume the frontend passes the history back or we use a simple temporary store
        self.sessions = {} 

    def start_session(self, user_id: str) -> str:
        """Starts a new character creation session and returns a session ID."""
        session_id = str(ObjectId())
        self.sessions[session_id] = {
            "user_id": user_id,
            "messages": [
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                }
            ],
            "facts": {},
            "created_at": datetime.now(UTC)
        }
        return session_id

    def get_ai_response(self, session_id: str, user_message: str) -> str:
        """Processes a user message and returns the AI's response."""
        if session_id not in self.sessions:
            raise ValueError("Session not found")

        session = self.sessions[session_id]
        session["messages"].append({"role": "user", "content": user_message})

        # Extract facts periodically (every 3 messages)
        if len(session["messages"]) % 3 == 0:
            session["facts"] = self.memory_manager.extract_facts(
                session["messages"],
                self.ai_client
            )
        
        # Build optimized context using memory manager
        optimized_context = self.memory_manager.build_context(
            session["messages"],
            session.get("facts", {})
        )

        # Generate response using optimized context
        response = self.ai_client.generate_completion(
            messages=optimized_context,
            temperature=0.7,
            max_tokens=2000
        )

        session["messages"].append({"role": "assistant", "content": response})
        return response

    def finalize_character(self, session_id: str) -> Dict[str, Any]:
        """Extracts structured character data from the conversation history."""
        if session_id not in self.sessions:
            raise ValueError("Session not found")

        session = self.sessions[session_id]
        
        # Call AI to extract structured data
        extraction_prompt = "Based on the conversation above, extract the character details in JSON format. Include: name, description, background, personality, appearance, and any other relevant traits."
        
        # We can use extract_structured_data if available in AIClient
        # Assuming AIClient has a method to extract into a specific schema
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "background": {"type": "string"},
                "personality": {"type": "string"},
                "appearance": {"type": "string"},
                "traits": {"type": "array", "items": {"type": "string"}},
                "speaking_style": {"type": "string"}
            },
            "required": ["name", "description"]
        }

        # For simplicity in this demo, we'll use generate_completion with a strict prompt
        # but in production we'd use function calling or structured output.
        extracted_data = self.ai_client.extract_structured_data(
            messages=session["messages"] + [{"role": "user", "content": extraction_prompt}],
            schema=schema
        )

        return extracted_data

    def _get_system_prompt(self) -> str:
        return """You are an expert character creator assistant. Your goal is to help the user design a rich, compelling character for a story or roleplay.
        
Interact with the user naturally. Ask questions about the character's background, personality, goals, and appearance. 
Don't ask everything at once; keep the conversation engaging.
Once you have enough information, you can offer suggestions or refine details.

Your persona: Creative, inquisitive, and supportive."""

# Note: In a production environment, self.sessions would be a MongoDB collection.
