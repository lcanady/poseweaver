import pytest
from app.services.model_config import ModelConfig, ModelConfigError


class TestModelConfig:
    """Test suite for model configuration service."""
    
    def test_get_dolphin_config(self):
        """Test getting Dolphin model configuration."""
        config = ModelConfig.get_dolphin_config()
        
        assert config["model"] == "dolphin-2.9-llama3-70b"
        assert config["temperature"] == 0.7
        assert config["max_tokens"] == 1000
        assert config["supports_thinking"] is True
        assert config["description"] == "Uncensored model based on Llama3 70B"
    
    def test_get_dolphin_config_with_overrides(self):
        """Test getting Dolphin config with parameter overrides."""
        config = ModelConfig.get_dolphin_config(
            temperature=0.9,
            max_tokens=500
        )
        
        assert config["model"] == "dolphin-2.9-llama3-70b"
        assert config["temperature"] == 0.9
        assert config["max_tokens"] == 500
        assert config["supports_thinking"] is True
    
    def test_get_model_config_dolphin(self):
        """Test getting model config for Dolphin model."""
        config = ModelConfig.get_model_config("dolphin-2.9-llama3-70b")
        
        assert config["model"] == "dolphin-2.9-llama3-70b"
        assert config["supports_thinking"] is True
        assert config["max_context"] == 8192
    
    def test_get_model_config_unknown_model(self):
        """Test getting config for unknown model."""
        config = ModelConfig.get_model_config("unknown-model")
        
        assert config["model"] == "unknown-model"
        assert config["supports_thinking"] is False
        assert config["max_context"] == 4096
        assert config["temperature"] == 0.7
    
    def test_is_valid_model_valid_models(self):
        """Test validation of valid model names."""
        valid_models = [
            "dolphin-2.9-llama3-70b",
            "gpt-3.5-turbo",
            "claude-3-opus"
        ]
        
        for model in valid_models:
            assert ModelConfig.is_valid_model(model) is True
    
    def test_is_valid_model_invalid_models(self):
        """Test validation of invalid model names."""
        invalid_models = [
            "",
            None,
            "invalid/model",
            "model with spaces",
            "model@special"
        ]
        
        for model in invalid_models:
            assert ModelConfig.is_valid_model(model) is False
    
    def test_get_available_models(self):
        """Test getting list of available models."""
        models = ModelConfig.get_available_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert "dolphin-2.9-llama3-70b" in models
    
    def test_get_model_presets(self):
        """Test getting model presets."""
        presets = ModelConfig.get_model_presets()
        
        assert isinstance(presets, dict)
        assert "dolphin_creative" in presets
        assert "dolphin_balanced" in presets
        assert "dolphin_precise" in presets
        
        # Test dolphin_creative preset
        creative = presets["dolphin_creative"]
        assert creative["model"] == "dolphin-2.9-llama3-70b"
        assert creative["temperature"] == 0.9
        assert creative["description"] == "High creativity for roleplay"
    
    def test_get_preset_config(self):
        """Test getting configuration for a specific preset."""
        config = ModelConfig.get_preset_config("dolphin_creative")
        
        assert config["model"] == "dolphin-2.9-llama3-70b"
        assert config["temperature"] == 0.9
        assert config["max_tokens"] == 1000
    
    def test_get_preset_config_unknown_preset(self):
        """Test getting config for unknown preset."""
        with pytest.raises(ModelConfigError) as exc_info:
            ModelConfig.get_preset_config("unknown_preset")
        
        assert "Unknown preset" in str(exc_info.value)
    
    def test_validate_config_valid(self):
        """Test validation of valid configuration."""
        valid_config = {
            "model": "dolphin-2.9-llama3-70b",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        assert ModelConfig.validate_config(valid_config) is True
    
    def test_validate_config_invalid_temperature(self):
        """Test validation with invalid temperature."""
        invalid_config = {
            "model": "dolphin-2.9-llama3-70b",
            "temperature": 1.5,  # Invalid
            "max_tokens": 1000
        }
        
        with pytest.raises(ModelConfigError) as exc_info:
            ModelConfig.validate_config(invalid_config)
        
        assert "Temperature must be between 0.0 and 1.0" in str(exc_info.value)
    
    def test_validate_config_invalid_max_tokens(self):
        """Test validation with invalid max_tokens."""
        invalid_config = {
            "model": "dolphin-2.9-llama3-70b",
            "temperature": 0.7,
            "max_tokens": 5000  # Invalid
        }
        
        with pytest.raises(ModelConfigError) as exc_info:
            ModelConfig.validate_config(invalid_config)
        
        assert "max_tokens must be between 1 and 4000" in str(exc_info.value)
    
    def test_validate_config_missing_required_field(self):
        """Test validation with missing required field."""
        invalid_config = {
            "temperature": 0.7,
            "max_tokens": 1000
            # Missing model
        }
        
        with pytest.raises(ModelConfigError) as exc_info:
            ModelConfig.validate_config(invalid_config)
        
        assert "Missing required field: model" in str(exc_info.value)
    
    def test_create_system_message_for_roleplay(self):
        """Test creating system message for roleplay context."""
        system_msg = ModelConfig.create_system_message_for_roleplay()
        
        assert isinstance(system_msg, str)
        assert "roleplay" in system_msg.lower()
        assert "creative" in system_msg.lower()
        assert "storyteller" in system_msg.lower()
        assert "human-like" in system_msg.lower()
        assert "narrative" in system_msg.lower()
    
    def test_create_system_message_for_character_analysis(self):
        """Test creating system message for character analysis."""
        system_msg = ModelConfig.create_system_message_for_character_analysis()
        
        assert isinstance(system_msg, str)
        assert "character" in system_msg.lower()
        assert "analyst" in system_msg.lower()
        assert "structured" in system_msg.lower() 