"""
Memory Manager Service for AI Chat Sessions.

Implements Phase 1 memory enhancement:
- Sliding window context management
- Character fact extraction
- Conversation summarization
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
import json


class MemoryManagerService:
    """Manages conversation memory for AI character creation sessions."""
    
    def __init__(self, window_size: int = 6, max_summary_messages: int = 20):
        """
        Initialize memory manager.
        
        Args:
            window_size: Number of recent messages to keep in full detail
            max_summary_messages: Number of old messages to summarize
        """
        self.window_size = window_size
        self.max_summary_messages = max_summary_messages
    
    def extract_facts(self, messages: List[Dict[str, str]], ai_client) -> Dict[str, Any]:
        """
        Extract structured character facts from conversation.
        
        Args:
            messages: Conversation history
            ai_client: AIClient instance for extraction
            
        Returns:
            Dictionary of character facts
        """
        if len(messages) < 2:
            return {}
        
        # Build extraction prompt
        conversation_text = self._format_messages_for_extraction(messages)
        
        schema = {
            "name": "Character name if mentioned",
            "traits": "List of personality traits",
            "appearance": "Physical description",
            "background": "Background or origin story",
            "goals": "Character goals or motivations",
            "speaking_style": "How the character speaks"
        }
        
        try:
            facts = ai_client.extract_structured_data(
                unstructured_text=conversation_text,
                schema=schema,
                max_tokens=1000
            )
            return facts
        except Exception as e:
            # Fallback: return empty dict if extraction fails
            return {}
    
    def build_context(
        self,
        messages: List[Dict[str, str]],
        facts: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        Build optimized context from full conversation history.
        
        Strategy:
        1. Keep recent N messages in full
        2. Summarize older messages
        3. Prepend character facts
        
        Args:
            messages: Full conversation history
            facts: Extracted character facts
            
        Returns:
            Optimized message list for context window
        """
        if len(messages) <= self.window_size:
            # Conversation is short, return as-is
            return messages
        
        # Split into recent and old
        recent_messages = messages[-self.window_size:]
        old_messages = messages[1:-self.window_size]  # Skip system message
        
        # Summarize old messages
        summary = self._summarize_messages(old_messages)
        
        # Build optimized context
        context = [messages[0]]  # Keep system message
        
        # Add facts as a system message if available
        if facts and any(facts.values()):
            facts_text = self._format_facts(facts)
            context.append({
                "role": "system",
                "content": f"Character details so far:\n{facts_text}"
            })
        
        # Add summary of old messages
        if summary:
            context.append({
                "role": "system",
                "content": f"Earlier conversation summary:\n{summary}"
            })
        
        # Add recent messages in full
        context.extend(recent_messages)
        
        return context
    
    def _format_messages_for_extraction(self, messages: List[Dict[str, str]]) -> str:
        """Format conversation for fact extraction."""
        formatted = []
        for msg in messages:
            if msg["role"] == "user":
                formatted.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant":
                formatted.append(f"Assistant: {msg['content']}")
        return "\n".join(formatted)
    
    def _summarize_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Create a concise summary of message exchanges.
        
        For now, this is a simple extraction approach.
        In Phase 2, we could use AI to generate smarter summaries.
        """
        if not messages:
            return ""
        
        # Simple extraction: pull key points from user messages
        key_points = []
        for msg in messages:
            if msg["role"] == "user":
                content = msg["content"]
                # Simple heuristic: if it's short, it's likely important
                if len(content) < 100:
                    key_points.append(content)
        
        if key_points:
            return "User mentioned: " + "; ".join(key_points[:5])
        return "Discussed character details"
    
    def _format_facts(self, facts: Dict[str, Any]) -> str:
        """Format facts into readable text."""
        lines = []
        for key, value in facts.items():
            if value:
                if isinstance(value, list):
                    lines.append(f"- {key.replace('_', ' ').title()}: {', '.join(value)}")
                else:
                    lines.append(f"- {key.replace('_', ' ').title()}: {value}")
        return "\n".join(lines) if lines else "None extracted yet"
    
    def estimate_token_count(self, messages: List[Dict[str, str]]) -> int:
        """
        Rough estimate of token count for messages.
        
        Uses simple heuristic: ~4 characters per token.
        For more accuracy in Phase 2, use tiktoken.
        """
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        return total_chars // 4
