# Marketplace Plugin Examples

This document provides example plugin manifests demonstrating the JSON Schema
config system.

## Example 1: Dice Roller Plugin

A plugin that adds dice rolling functionality to poses.

### Plugin Manifest

```python
{
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Dice Roller",
    "description": "Add RPG-style dice rolling to your scenes. Automatically rolls dice on pose generation or manually trigger rolls.",
    "price": 499,  # $4.99
    "hooks": ["ON_POSE", "ON_SCENE_START"],
    "config_schema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "title": "Dice Roller Configuration",
        "properties": {
            "dice_type": {
                "type": "string",
                "title": "Dice Type",
                "enum": ["d4", "d6", "d8", "d10", "d12", "d20", "d100"],
                "default": "d20",
                "description": "Default dice type for rolls"
            },
            "auto_roll": {
                "type": "boolean",
                "title": "Auto Roll on Pose",
                "default": false,
                "description": "Automatically roll dice when a new pose is generated"
            },
            "critical_threshold": {
                "type": "integer",
                "title": "Critical Hit Threshold",
                "minimum": 1,
                "maximum": 20,
                "default": 20,
                "description": "Roll result that triggers a critical success"
            },
            "show_history": {
                "type": "boolean",
                "title": "Show Roll History",
                "default": true,
                "description": "Display history of all dice rolls in the scene"
            }
        },
        "required": ["dice_type"]
    },
    "code_ref": "plugins/dice_roller/main.py",
    "is_official": true,
    "author": "PoseWeaver Team",
    "version": "1.0.0"
}
```

### User Settings Example

When a user configures this plugin, their settings might look like:

```python
{
    "dice_type": "d20",
    "auto_roll": true,
    "critical_threshold": 18,
    "show_history": true
}
```

---

## Example 2: Weather Effects Plugin

A free plugin that adds atmospheric weather to scenes.

### Plugin Manifest

```python
{
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "name": "Weather Effects",
    "description": "Add dynamic weather conditions to your scenes with customizable effects.",
    "price": 0,  # Free
    "hooks": ["ON_SCENE_START", "ON_POSE"],
    "config_schema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "title": "Weather Effects Configuration",
        "properties": {
            "weather_type": {
                "type": "string",
                "title": "Weather Type",
                "enum": ["clear", "rain", "snow", "fog", "storm", "random"],
                "default": "clear",
                "description": "Type of weather effect to apply"
            },
            "intensity": {
                "type": "number",
                "title": "Effect Intensity",
                "minimum": 0,
                "maximum": 1,
                "default": 0.5,
                "description": "Intensity of weather effects (0 = subtle, 1 = extreme)"
            },
            "dynamic_weather": {
                "type": "boolean",
                "title": "Dynamic Weather",
                "default": false,
                "description": "Weather changes randomly throughout the scene"
            },
            "temperature_display": {
                "type": "boolean",
                "title": "Show Temperature",
                "default": true,
                "description": "Display temperature reading in scene"
            }
        },
        "required": ["weather_type"]
    },
    "code_ref": "plugins/weather_effects/main.py",
    "is_official": true,
    "author": "PoseWeaver Team",
    "version": "2.1.0"
}
```

---

## Example 3: Advanced Storytelling Plugin

Premium plugin with complex nested configuration.

### Plugin Manifest

```python
{
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "name": "Advanced Storytelling",
    "description": "AI-powered narrative enhancement with multiple story modes and character development tracking.",
    "price": 1999,  # $19.99
    "hooks": ["ON_POSE", "ON_SCENE_START", "ON_CHARACTER_CREATE"],
    "config_schema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "title": "Advanced Storytelling Configuration",
        "properties": {
            "narrative_mode": {
                "type": "string",
                "title": "Narrative Mode",
                "enum": ["first_person", "third_person_limited", "third_person_omniscient"],
                "default": "third_person_limited",
                "description": "Point of view for generated narrative"
            },
            "story_complexity": {
                "type": "integer",
                "title": "Story Complexity",
                "minimum": 1,
                "maximum": 5,
                "default": 3,
                "description": "Complexity level of generated plots (1=simple, 5=intricate)"
            },
            "character_development": {
                "type": "object",
                "title": "Character Development Settings",
                "properties": {
                    "track_relationships": {
                        "type": "boolean",
                        "title": "Track Character Relationships",
                        "default": true
                    },
                    "personality_evolution": {
                        "type": "boolean",
                        "title": "Enable Personality Evolution",
                        "default": true,
                        "description": "Characters evolve based on story events"
                    },
                    "memory_depth": {
                        "type": "integer",
                        "title": "Memory Depth",
                        "minimum": 5,
                        "maximum": 50,
                        "default": 20,
                        "description": "Number of past events characters remember"
                    }
                }
            },
            "themes": {
                "type": "array",
                "title": "Story Themes",
                "items": {
                    "type": "string",
                    "enum": ["adventure", "mystery", "romance", "horror", "comedy", "drama"]
                },
                "default": ["adventure"],
                "description": "Themes to emphasize in the narrative"
            },
            "auto_generate_twists": {
                "type": "boolean",
                "title": "Auto-Generate Plot Twists",
                "default": false,
                "description": "Automatically introduce plot twists at key moments"
            }
        },
        "required": ["narrative_mode", "story_complexity"]
    },
    "code_ref": "plugins/advanced_storytelling/main.py",
    "is_official": true,
    "author": "PoseWeaver Team",
    "version": "3.0.0"
}
```

### User Settings Example

```python
{
    "narrative_mode": "first_person",
    "story_complexity": 4,
    "character_development": {
        "track_relationships": true,
        "personality_evolution": true,
        "memory_depth": 30
    },
    "themes": ["mystery", "drama"],
    "auto_generate_twists": true
}
```

---

## JSON Schema to UI Mapping Guide

### Field Type Mappings

| JSON Schema Type     | UI Component             | Notes                    |
| -------------------- | ------------------------ | ------------------------ |
| `string`             | Text Input               | Default for string types |
| `string` with `enum` | Select/Dropdown          | Options from enum array  |
| `boolean`            | Toggle/Checkbox          | On/off switch            |
| `integer`            | Number Input             | With min/max validation  |
| `number`             | Number Input             | Supports decimals        |
| `object`             | Nested Section           | Collapsible subsection   |
| `array`              | Multi-select or Repeater | Depends on items type    |

### Schema Properties Used

- **`title`**: Label shown next to the input field
- **`description`**: Help text or tooltip content
- **`default`**: Pre-filled value when user first configures
- **`enum`**: Available options for select fields
- **`minimum`/`maximum`**: Validation bounds for numbers
- **`required`**: Fields in this array must be filled

### Validation Rules

The frontend should validate:

1. Required fields are non-empty
2. Numbers are within min/max bounds
3. Enum values match one of the allowed options
4. Object properties follow nested schema rules

---

## Creating a New Plugin

To add a new plugin to the marketplace:

1. **Create the plugin code** in your backend
2. **Define the config schema** following JSON Schema draft-07
3. **Create a PluginManifest record**:

```python
from app.models.marketplace import PluginManifest

plugin = PluginManifest(
    name="My Plugin",
    description="Plugin description",
    price=999,  # $9.99 or 0 for free
    hooks=["ON_POSE"],
    config_schema={
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            # Your schema here
        }
    },
    code_ref="plugins/my_plugin/main.py",
    is_official=True,
    author="Your Name",
    version="1.0.0"
)
plugin.save()
```

4. **Set up Stripe product/price** (if not free)
5. **Update plugin with Stripe IDs**:

```python
plugin.stripe_product_id = "prod_YourProductId"
plugin.stripe_price_id = "price_YourPriceId"
plugin.save()
```
