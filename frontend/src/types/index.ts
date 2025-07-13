// Character-related types
export interface CharacterData {
  background: string
  personality: string[]
  skills?: string[]
  motivations?: string[]
  relationships?: string[]
  physical_description?: string
  psychological_traits?: string[]
}

// Pose context types
export interface PoseContext {
  actions: string[]
  emotions: string[]
  environmental_details: string[]
  character_interactions: string[]
  response_hooks: string[]
}

// API request/response types
export interface BrainDumpRequest {
  dump: string
  model?: string
  temperature?: number
  max_tokens?: number
}

export interface PoseContextRequest {
  pose: string
  model?: string
  temperature?: number
}

export interface PoseGenerationRequest {
  prompt: string
  character_info: Partial<CharacterData>
  pose_context: Partial<PoseContext>
  model?: string
  temperature?: number
  max_tokens?: number
}

export interface GeneratedPose {
  enhanced_pose: string
}

// API configuration types
export interface APIConfig {
  model: string
  temperature: number
  max_tokens: number
}

// Error types
export interface APIError {
  error: string
  status?: number
}

// Component prop types
export interface LoadingState {
  isLoading: boolean
  message?: string
}

export interface ErrorState {
  hasError: boolean
  message?: string
} 