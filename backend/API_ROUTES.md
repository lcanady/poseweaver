# MUSH Pose Editor Backend API Routes

This document provides a comprehensive overview of all API endpoints available in the MUSH Pose Editor backend.

## Base Configuration

- **Base URL**: `http://localhost:5001` (development)
- **Content-Type**: `application/json` for all POST requests
- **CORS**: Enabled for frontend origins (`localhost:3000`, `localhost:5173`)

## Health Check

### GET `/health`
Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "mush-pose-editor"
}
```

---

## Character Management (`/api/characters`)

### POST `/api/characters/process`
Process a character brain dump into structured profile data.

**Request Body:**
```json
{
  "brain_dump": "Free-form character description text...",
  "existing_character": {  // Optional
    "name": "Character Name",
    "background": "Character background...",
    "personality": ["trait1", "trait2"],
    "skills": ["skill1", "skill2"],
    "goals": ["goal1", "goal2"],
    "relationships": {"name": "relationship_type"},
    "voice_notes": "How character speaks..."
  }
}
```

**Response:**
```json
{
  "success": true,
  "character": {
    "name": "Character Name",
    "background": "Processed background...",
    "personality": ["trait1", "trait2"],
    "skills": ["skill1", "skill2"],
    "goals": ["goal1", "goal2"],
    "relationships": {"name": "relationship_type"},
    "voice_notes": "Speaking style notes..."
  }
}
```

### POST `/api/characters/validate`
Validate character profile data structure.

**Request Body:**
```json
{
  "character": {
    "name": "Character Name",
    "background": "...",
    "personality": ["..."],
    "skills": ["..."],
    "goals": ["..."],
    "relationships": {},
    "voice_notes": "..."
  }
}
```

**Response:**
```json
{
  "success": true,
  "valid": true,
  "errors": []
}
```

### GET `/api/characters/schema`
Get the character profile data schema definition.

**Response:**
```json
{
  "success": true,
  "schema": {
    "fields": {
      "name": {
        "type": "string",
        "required": true,
        "description": "Character's full name"
      },
      // ... other field definitions
    }
  }
}
```

---

## Context Analysis (`/api/context`)

### POST `/api/context/analyze`
Analyze a pose to extract context for response crafting.

**Request Body:**
```json
{
  "pose_text": "The pose text to analyze...",
  "character_name": "Optional character name for perspective"
}
```

**Response:**
```json
{
  "success": true,
  "context": {
    "actions": ["action1", "action2"],
    "emotions": ["emotion1", "emotion2"],
    "environmental_details": ["detail1", "detail2"],
    "character_interactions": ["interaction1"],
    "response_hooks": ["hook1", "hook2"],
    "scene_timing": "timing_description",
    "urgency_level": "low|medium|high",
    "narrative_tone": "tone_description"
  },
  "suggestions": ["suggestion1", "suggestion2"]
}
```

### POST `/api/context/analyze-multiple`
Analyze multiple poses and return context for each.

**Request Body:**
```json
{
  "poses": ["pose1", "pose2", "pose3"],  // Max 10 poses
  "character_name": "Optional character name"
}
```

**Response:**
```json
{
  "success": true,
  "results": {
    "pose_0": { /* context analysis */ },
    "pose_1": { /* context analysis */ },
    "pose_2": { /* context analysis */ }
  }
}
```

---

## Pose Enhancement (`/api/pose`)

### POST `/api/pose/enhance`
Enhance a basic pose into rich narrative.

**Request Body:**
```json
{
  "original_pose": "Basic pose text...",
  "character": {  // Optional
    "name": "Character Name",
    "background": "...",
    "personality": ["..."],
    "skills": ["..."],
    "goals": ["..."],
    "relationships": {},
    "voice_notes": "..."
  },
  "context": {  // Optional
    "actions": ["..."],
    "emotions": ["..."],
    "environmental_details": ["..."],
    "character_interactions": ["..."],
    "response_hooks": ["..."],
    "scene_timing": "...",
    "urgency_level": "...",
    "narrative_tone": "..."
  },
  "enhancement_style": "minimal|balanced|elaborate"  // Default: balanced
}
```

**Response:**
```json
{
  "success": true,
  "enhanced_pose": "Enhanced pose text with rich narrative..."
}
```

### POST `/api/pose/variations`
Generate multiple enhancement variations of a pose.

**Request Body:**
```json
{
  "original_pose": "Basic pose text...",
  "character": {  // Optional character profile
    "name": "Character Name"
    // ... other character fields
  },
  "count": 3  // Number of variations (1-3, default: 3)
}
```

**Response:**
```json
{
  "success": true,
  "variations": [
    {
      "original_pose": "...",
      "enhanced_pose": "...",
      "enhancement_style": "...",
      "word_count": 25,
      "has_dialogue": true,
      "has_action": true
    },
    // ... more variations
  ]
}
```

### POST `/api/pose/analyze`
Analyze the quality and characteristics of a pose.

**Request Body:**
```json
{
  "pose": "Pose text to analyze...",
  "character": {  // Optional character profile
    "name": "Character Name"
    // ... other character fields
  }
}
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "word_count": 25,
    "sentence_count": 2,
    "has_dialogue": true,
    "has_action": true,
    "has_emotion": false,
    "complexity_score": 5,
    "character_consistency": true  // if character provided
  }
}
```

### POST `/api/pose/parse-mush-output`
Parse MUSH game output and extract character poses.

**Request Body:**
```json
{
  "mush_output": "Raw MUSH output text",
  "your_character_name": "Your character's name",
  "character": {  // Optional character profile
    "name": "Character Name"
    // ... other character fields
  },
  "enhancement_style": "minimal|balanced|elaborate",  // Optional
  "skip_enhancement": false  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "parsed_scene": {
    "room_description": "...",
    "characters_present": ["char1", "char2"],
    "your_character": "your_char_name",
    "poses": [
      {
        "character_name": "...",
        "content": "...",
        "pose_type": "action|dialogue|narrative|internal|mixed",
        "is_ooc": false,
        "timestamp": "..."
      }
    ]
  },
  "your_poses": ["pose1", "pose2"],
  "enhanced_poses": ["enhanced1", "enhanced2"],
  "scene_context": "Context description..."
}
```

---

## MUSH Parser (`/api/mush`)

### POST `/api/mush/parse`
Parse MUSH game output into structured data.

**Request Body:**
```json
{
  "mush_output": "Raw MUSH output text",
  "your_character_hint": "Optional hint about your character name"
}
```

**Response:**
```json
{
  "room_description": "Room description text",
  "characters_present": ["character1", "character2"],
  "your_character": "your_character_name",
  "poses": [
    {
      "character_name": "Character Name",
      "content": "Pose content",
      "pose_type": "action|dialogue|narrative|internal|mixed",
      "is_ooc": false,
      "timestamp": "timestamp_string"
    }
  ]
}
```

### POST `/api/mush/enhance`
Parse MUSH output and enhance your character's poses with scene context.

**Request Body:**
```json
{
  "mush_output": "Raw MUSH output text",
  "your_character_name": "Your character name",
  "character": {
    "name": "Character Name",
    "background": "...",
    "personality": ["trait1", "trait2"],
    "speaking_style": "...",
    "physical_description": "..."
  },
  "enhancement_style": "balanced|detailed|subtle"  // Default: balanced
}
```

**Response:**
```json
{
  "success": true,
  "parsed_scene": { /* scene data */ },
  "enhanced_poses": [
    {
      "original": "Original pose text",
      "enhanced": "Enhanced pose text",
      "character_name": "Character Name"
    }
  ],
  "scene_context": "Overall scene context description"
}
```

### GET `/api/mush/help`
Get help information about MUSH parsing capabilities.

**Response:**
```json
{
  "description": "MUSH Parser allows you to copy and paste MUSH game output for automatic pose enhancement",
  "supported_formats": [
    "Standard poses: 'CharacterName does something'",
    "Dialogue: 'CharacterName says, \"something\"'",
    "OOC comments: '<OOC> CharacterName says, \"something\"'",
    "Room descriptions with ---- headers",
    "Character lists in Contents: sections",
    "Timestamped output"
  ],
  "endpoints": {
    "/parse": "Parse MUSH output into structured data",
    "/enhance": "Parse and enhance your character's poses with scene context",
    "/preview": "Preview parsing results without enhancement"
  },
  "tips": [
    "Include room descriptions and character lists for better context",
    "Make sure to specify your exact character name",
    "The parser will automatically detect pose types and build scene context",
    "OOC comments are preserved but not enhanced"
  ]
}
```

---

## Scene Flow Management (`/api/scene-flow`)

### POST `/api/scene-flow/scenes`
Create a new scene flow.

**Request Body:**
```json
{
  "name": "Scene name",
  "character_name": "Main character name"
}
```

**Response:**
```json
{
  "success": true,
  "scene": {
    "id": "scene_uuid",
    "name": "Scene name",
    "character_name": "Main character name",
    "poses": [],
    "created_at": "timestamp",
    "updated_at": "timestamp"
  }
}
```

### GET `/api/scene-flow/scenes`
List all active scenes.

**Response:**
```json
{
  "success": true,
  "scenes": [
    {
      "id": "scene_uuid",
      "name": "Scene name",
      "character_name": "Character name",
      "pose_count": 5,
      "created_at": "timestamp",
      "updated_at": "timestamp"
    }
  ]
}
```

### POST `/api/scene-flow/scenes/{scene_id}/poses`
Add a new pose to a scene.

**Request Body:**
```json
{
  "character_name": "Character name",
  "pose_text": "Pose text",
  "pose_type": "action|dialogue|narrative|internal|mixed"  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "pose": {
    "id": "pose_uuid",
    "character_name": "Character name",
    "content": "Pose text",
    "pose_type": "action",
    "timestamp": "timestamp",
    "is_ooc": false
  },
  "scene": {
    "id": "scene_uuid",
    "name": "Scene name",
    // ... scene data with updated poses
  }
}
```

### POST `/api/scene-flow/scenes/{scene_id}/poses/bulk`
Bulk import multiple poses to a scene.

**Request Body:**
```json
{
  "poses_text": "Multi-line text with poses",
  "format": "simple|character_prefix|mush_output"  // Default: simple
}
```

**Format Options:**
- `simple`: Each line is a pose, character name extracted from start
- `character_prefix`: Lines like "CharacterName: pose text"
- `mush_output`: Raw MUSH game output with name separators and OOC

**Response:**
```json
{
  "success": true,
  "imported_count": 5,
  "poses": [
    {
      "id": "pose_uuid",
      "character_name": "Character name",
      "content": "Pose text",
      "pose_type": "action",
      "timestamp": "timestamp",
      "is_ooc": false
    }
  ]
}
```

### GET `/api/scene-flow/health`
Health check for scene flow service.

**Response:**
```json
{
  "success": true,
  "service": "scene_flow",
  "status": "healthy",
  "active_scenes": 3
}
```

---

## Model Configuration (`/api/models`)

### GET `/api/models/presets`
Get all available model presets.

**Response:**
```json
{
  "presets": {
    "creative": {
      "model": "dolphin-2.9-llama3-70b",
      "temperature": 0.9,
      "max_tokens": 1500
    },
    "balanced": {
      "model": "dolphin-2.9-llama3-70b",
      "temperature": 0.7,
      "max_tokens": 1000
    },
    "precise": {
      "model": "dolphin-2.9-llama3-70b",
      "temperature": 0.3,
      "max_tokens": 800
    }
  }
}
```

### GET `/api/models/available`
Get list of available models.

**Response:**
```json
{
  "models": [
    "dolphin-2.9-llama3-70b",
    "llama-3.1-70b-instruct",
    "mixtral-8x7b-instruct"
  ]
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "success": false,
  "error": "Descriptive error message"
}
```

### 404 Not Found
```json
{
  "success": false,
  "error": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Internal server error: detailed message"
}
```

### 503 Service Unavailable
```json
{
  "success": false,
  "error": "AI processing failed: service temporarily unavailable"
}
```

---

## Development Notes

### Environment Variables
Required environment variables (see `env.example`):
- `VENICE_API_KEY`: Venice.ai API key for AI processing
- `FLASK_ENV`: Environment mode (development/production)
- `FLASK_DEBUG`: Debug mode flag
- `SECRET_KEY`: Flask secret key

### Testing
- Run tests with: `make test` or `pytest`
- Test files located in `backend/tests/`
- Each API module has corresponding test files

### CORS Configuration
The backend is configured to accept requests from:
- `http://localhost:3000` (React development server)
- `http://localhost:5173` (Vite development server)

### Rate Limiting
- Multiple pose analysis limited to 10 poses per request
- Pose variations limited to 3 variations per request

### AI Processing
All AI-enhanced endpoints use Venice.ai's Dolphin uncensored thinking model for:
- Character brain dump processing
- Pose enhancement and generation
- Context analysis and suggestions
- MUSH output parsing and enhancement 