"""
Tests for MemoryManagerService to verify memory management functionality.
"""

import pytest
from app.services.memory_manager_service import MemoryManagerService
from app.services.ai_client import AIClient


class TestMemoryManagerService:
    """Test suite for MemoryManagerService."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.memory_manager = MemoryManagerService(window_size=3, max_summary_messages=10)
        # Use mock AI client for testing
        self.ai_client = AIClient(api_key="mock_key_test")
    
    def test_short_conversation_no_compression(self):
        """Test that short conversations pass through unchanged."""
        messages = [
            {"role": "system", "content": "You are a character creator"},
            {"role": "user", "content": "Make a wizard"},
            {"role": "assistant", "content": "Great! Tell me more"}
        ]
        
        context = self.memory_manager.build_context(messages)
        
        # Should return same messages for short conversation
        assert len(context) == len(messages)
        assert context == messages
    
    def test_sliding_window_compression(self):
        """Test that long conversations are compressed to sliding window."""
        messages = [
            {"role": "system", "content": "You are a character creator"},
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "Message 2"},
            {"role": "assistant", "content": "Response 2"},
            {"role": "user", "content": "Message 3"},
            {"role": "assistant", "content": "Response 3"},
            {"role": "user", "content": "Message 4"},
            {"role": "assistant", "content": "Response 4"},
        ]
        
        context = self.memory_manager.build_context(messages)
        
        # Should compress: system + summary + last 3 messages (window_size=3)
        assert len(context) < len(messages)
        
        # System message should be first
        assert context[0]["role"] == "system"
        assert context[0]["content"] == "You are a character creator"
        
        # Should contain recent messages
        assert context[-1] == messages[-1]
        assert context[-2] == messages[-2]
    
    def test_fact_extraction(self):
        """Test basic fact extraction from conversation."""
        messages = [
            {"role": "system", "content": "You are a character creator"},
            {"role": "user", "content": "I want a wizard named Gandalf"},
            {"role": "assistant", "content": "Great! Tell me about Gandalf's appearance"},
            {"role": "user", "content": "He has a long grey beard and wears robes"}
        ]
        
        facts = self.memory_manager.extract_facts(messages, self.ai_client)
        
        # With mock AI, should return a dictionary
        assert isinstance(facts, dict)
    
    def test_facts_included_in_context(self):
        """Test that extracted facts are included in context."""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "Message 2"},
            {"role": "assistant", "content": "Response 2"},
            {"role": "user", "content": "Message 3"},
            {"role": "assistant", "content": "Response 3"},
            {"role": "user", "content": "Message 4"},
        ]
        
        facts = {"name": "Gandalf", "traits": ["wise", "powerful"]}
        context = self.memory_manager.build_context(messages, facts)
        
        # Should include facts as a system message
        fact_messages = [msg for msg in context if "Character details" in msg.get("content", "")]
        assert len(fact_messages) > 0
