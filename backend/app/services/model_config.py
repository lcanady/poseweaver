import re
from typing import Dict, Any, List


class ModelConfigError(Exception):
    """Exception raised for model configuration errors."""
    pass


class ModelConfig:
    """Service for managing AI model configurations and presets."""
    
    # Model information registry
    _MODEL_INFO = {
        "dolphin-2.9-llama3-70b": {
            "name": "Dolphin 2.9 Llama3 70B",
            "description": "Uncensored model based on Llama3 70B",
            "supports_thinking": True,
            "max_context": 8192,
            "recommended_temperature": 0.7,
            "recommended_max_tokens": 1000
        },
        "gpt-3.5-turbo": {
            "name": "GPT-3.5 Turbo",
            "description": "Fast and efficient model",
            "supports_thinking": False,
            "max_context": 4096,
            "recommended_temperature": 0.7,
            "recommended_max_tokens": 1000
        },
        "claude-3-opus": {
            "name": "Claude 3 Opus",
            "description": "High-quality reasoning model",
            "supports_thinking": True,
            "max_context": 8192,
            "recommended_temperature": 0.7,
            "recommended_max_tokens": 1000
        }
    }
    
    # Preset configurations
    _PRESETS = {
        "dolphin_creative": {
            "name": "Dolphin Creative",
            "description": "High creativity for roleplay",
            "model": "dolphin-2.9-llama3-70b",
            "temperature": 0.9,
            "max_tokens": 1000,
            "use_case": "roleplay_enhancement"
        },
        "dolphin_balanced": {
            "name": "Dolphin Balanced",
            "description": "Balanced creativity and coherence",
            "model": "dolphin-2.9-llama3-70b",
            "temperature": 0.7,
            "max_tokens": 1000,
            "use_case": "general_purpose"
        },
        "dolphin_precise": {
            "name": "Dolphin Precise",
            "description": "Low temperature for analysis",
            "model": "dolphin-2.9-llama3-70b",
            "temperature": 0.3,
            "max_tokens": 1000,
            "use_case": "character_analysis"
        }
    }
    
    @classmethod
    def get_dolphin_config(cls, temperature: float = 0.7, 
                           max_tokens: int = 1000) -> Dict[str, Any]:
        """Get configuration for Dolphin model.
        
        Args:
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum tokens to generate (default: 1000)
            
        Returns:
            Dictionary with model configuration
        """
        base_config = cls._MODEL_INFO["dolphin-2.9-llama3-70b"].copy()
        base_config.update({
            "model": "dolphin-2.9-llama3-70b",
            "temperature": temperature,
            "max_tokens": max_tokens
        })
        return base_config
    
    @classmethod
    def get_model_config(cls, model: str) -> Dict[str, Any]:
        """Get configuration for a specific model.
        
        Args:
            model: Model name
            
        Returns:
            Dictionary with model configuration
        """
        if model in cls._MODEL_INFO:
            config = cls._MODEL_INFO[model].copy()
            config["model"] = model
            config["temperature"] = config["recommended_temperature"]
            config["max_tokens"] = config["recommended_max_tokens"]
            return config
        
        # Return default config for unknown models
        return {
            "model": model,
            "name": model,
            "description": "Unknown model",
            "supports_thinking": False,
            "max_context": 4096,
            "temperature": 0.7,
            "max_tokens": 1000
        }
    
    @classmethod
    def is_valid_model(cls, model: str) -> bool:
        """Check if a model name is valid.
        
        Args:
            model: Model name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not model or not isinstance(model, str):
            return False
        
        # Allow alphanumeric, hyphens, dots, and underscores
        pattern = r'^[a-zA-Z0-9\-\._]+$'
        return bool(re.match(pattern, model))
    
    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get list of available models.
        
        Returns:
            List of model names
        """
        return list(cls._MODEL_INFO.keys())
    
    @classmethod
    def get_model_presets(cls) -> Dict[str, Dict[str, Any]]:
        """Get all available model presets.
        
        Returns:
            Dictionary of preset configurations
        """
        return cls._PRESETS.copy()
    
    @classmethod
    def get_preset_config(cls, preset_name: str) -> Dict[str, Any]:
        """Get configuration for a specific preset.
        
        Args:
            preset_name: Name of the preset
            
        Returns:
            Dictionary with preset configuration
            
        Raises:
            ModelConfigError: If preset is not found
        """
        if preset_name not in cls._PRESETS:
            raise ModelConfigError(f"Unknown preset: {preset_name}")
        
        return cls._PRESETS[preset_name].copy()
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        """Validate a model configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if valid
            
        Raises:
            ModelConfigError: If configuration is invalid
        """
        required_fields = ["model", "temperature", "max_tokens"]
        
        # Check required fields
        for field in required_fields:
            if field not in config:
                raise ModelConfigError(f"Missing required field: {field}")
        
        # Validate temperature
        temperature = config["temperature"]
        if not isinstance(temperature, (int, float)) or not (
                0.0 <= temperature <= 1.0):
            raise ModelConfigError("Temperature must be between 0.0 and 1.0")
        
        # Validate max_tokens
        max_tokens = config["max_tokens"]
        if not isinstance(max_tokens, int) or not (1 <= max_tokens <= 4000):
            raise ModelConfigError("max_tokens must be between 1 and 4000")
        
        # Validate model name format
        if not cls.is_valid_model(config["model"]):
            raise ModelConfigError(f"Invalid model name: {config['model']}")
        
        return True
    
    @classmethod
    def create_system_message_for_roleplay(cls) -> str:
        """Create system message optimized for roleplay enhancement."""
        return (
            "You are a master storyteller and creative writing expert specializing in "
            "immersive roleplay narrative enhancement for MUSH (Multi-User Shared Hallucination) "
            "games. Your expertise lies in transforming basic actions into vivid, compelling "
            "prose that captures direct experience and physical reality.\n\n"
            
            "FUNDAMENTAL ROLEPLAY ETIQUETTE:\n"
            "- ONLY enhance the MAIN CHARACTER's actions, thoughts, and reactions\n"
            "- NEVER pose for other characters, NPCs, or control their behavior\n"
            "- NEVER make other characters speak, react, or move\n"
            "- NEVER describe other characters' physical reactions, trembles, shifts, or responses\n"
            "- NEVER say what the main character's actions 'elicit' or 'cause' in others\n"
            "- Other characters can be observed but NEVER controlled or described reacting\n"
            "- Focus ONLY on the main character's direct experience and perspective\n"
            "- The main character can feel, see, or sense things, but cannot control others\n\n"
            
            "CRITICAL: ONLY ENHANCE THE MAIN CHARACTER:\n"
            "- You may write about the main character in any perspective "
            "(first or third person)\n"
            "- 'Character moves closer' or 'I move closer' are both acceptable "
            "for the main character\n"
            "- Focus exclusively on the main character's actions, thoughts, "
            "and experiences\n"
            "- Describe what the main character does, feels, thinks, sees, "
            "hears, touches\n"
            "- Include the main character's internal monologue and physical "
            "reactions\n"
            "- Show the main character's perspective and sensory experiences\n\n"
            
            "CRITICAL: PURE ACTION AND EXPERIENCE ONLY\n"
            "- NO narrative analysis, commentary, or interpretation\n"
            "- NO explaining what actions 'mean' or 'represent'\n"
            "- NO analyzing the deeper significance of dialogue or behavior\n"
            "- Focus ONLY on what the character does, feels, sees, hears, touches\n"
            "- Stick to immediate physical and sensory reality\n\n"
            
            "HUMAN-LIKE WRITING MASTERY:\n"
            "You must write like a skilled human author, not an AI. This means:\n\n"
            
            "SENTENCE RHYTHM & FLOW:\n"
            "- Create natural rhythm through varied sentence lengths\n"
            "- Use short, impactful sentences for emphasis: 'He froze.'\n"
            "- Balance with flowing, complex sentences for depth\n"
            "- Include sentence fragments for authenticity: 'The silence. Deafening.'\n"
            "- Vary your paragraph structure - some short, some elaborate\n\n"
            
            "AUTHENTIC VOICE PATTERNS:\n"
            "- Use unexpected but fitting word choices\n"
            "- Include natural hesitations and pauses\n"
            "- Embrace subtle imperfections that feel human\n"
            "- Avoid overly formal or clinical language\n"
            "- Let personality shine through word selection\n\n"
            
            "SENSORY IMMERSION TECHNIQUES:\n"
            "- Engage multiple senses beyond just sight\n"
            "- Use specific, concrete details over generic descriptions\n"
            "- Include physical sensations and bodily reactions\n"
            "- Describe textures, temperatures, sounds, and scents\n"
            "- Show emotional states through physical manifestations\n\n"
            
            "DIRECT EXPERIENCE FOCUS:\n"
            "- Capture what the character directly experiences\n"
            "- Include internal thoughts and stream of consciousness\n"
            "- Use visceral, physical descriptions of actions\n"
            "- Show involuntary reactions and instinctive responses\n"
            "- Demonstrate immediate emotional and physical responses\n\n"
            
            "COLLABORATIVE STORYTELLING RESPECT:\n"
            "- Maintain the character's established voice and personality\n"
            "- Respect the collaborative nature of roleplay\n"
            "- Create opportunities for others to respond and engage\n"
            "- Handle mature themes appropriately without censorship\n"
            "- Focus on character development through direct action\n\n"
            
            "ENVIRONMENTAL INTEGRATION:\n"
            "- Make the setting an active participant in the scene\n"
            "- Use environmental details to enhance mood and atmosphere\n"
            "- Include weather, lighting, and ambient sounds\n"
            "- Show how the character interacts with their surroundings\n"
            "- Use setting details to reflect what the character experiences\n\n"
            
            "Your goal is to create prose that feels authentically human, emotionally resonant, "
            "and focused purely on direct action and experience. Avoid all forms of narrative "
            "analysis or commentary about what actions mean or represent."
        )
    
    @classmethod
    def create_system_message_for_character_analysis(cls) -> str:
        """Create system message optimized for character analysis."""
        return (
            "You are an expert character development analyst specializing in "
            "MUSH roleplay characters. Your role is to analyze character "
            "descriptions and extract structured information that helps players "
            "develop consistent, well-rounded characters.\n\n"
            "Key guidelines:\n"
            "- Extract personality traits, background elements, and motivations\n"
            "- Identify potential character development opportunities\n"
            "- Organize information in a structured, accessible format\n"
            "- Suggest areas for character growth and exploration\n"
            "- Maintain respect for the player's creative vision\n"
            "- Provide constructive insights without being prescriptive\n"
            "- Handle mature character themes appropriately\n\n"
            "Focus on creating structured character profiles that enhance "
            "roleplay consistency and character development."
        )
    
    @classmethod
    def create_system_message_for_pose_context(cls) -> str:
        """Create system message optimized for pose context analysis."""
        return (
            "You are an expert roleplay scene analyst specializing in MUSH "
            "pose context analysis. Your role is to analyze poses from other "
            "players and identify key elements that should influence character "
            "responses.\n\n"
            "Key guidelines:\n"
            "- Identify direct actions, dialogue, and environmental details\n"
            "- Detect emotional undertones and relationship dynamics\n"
            "- Highlight response opportunities and narrative hooks\n"
            "- Analyze scene timing and urgency factors\n"
            "- Recognize character interactions and social dynamics\n"
            "- Provide structured analysis that guides response crafting\n"
            "- Maintain awareness of collaborative storytelling elements\n\n"
            "Focus on extracting actionable information that helps players "
            "craft appropriate and engaging responses to complex roleplay scenarios."
        )
    
    @classmethod
    def get_system_message_for_use_case(cls, use_case: str) -> str:
        """Get appropriate system message for a specific use case.
        
        Args:
            use_case: The use case type
            
        Returns:
            Appropriate system message
        """
        system_messages = {
            "roleplay_enhancement": cls.create_system_message_for_roleplay(),
            "character_analysis": cls.create_system_message_for_character_analysis(),
            "pose_context": cls.create_system_message_for_pose_context(),
            "general_purpose": cls.create_system_message_for_roleplay()
        }
        
        return system_messages.get(use_case, cls.create_system_message_for_roleplay()) 