/**
 * Types for scene context and pose analysis
 */

export interface Pose {
  character_name: string;
  content: string;
  preview: string;
  is_ooc?: boolean;
  timestamp?: string;
}

export interface PoseContext {
  actions: string[];
  character_interactions: string[];
  emotions: string[];
  environmental_details: string[];
  responseHooks: string[];
  scene_timing?: string;
  urgency_level?: 'high' | 'medium' | 'low';
  urgency?: 'high' | 'medium' | 'low'; // Support for both field names
  narrative_tone?: string;
  tone?: string; // Support for both field names
  poses?: Pose[]; // Array of poses with collapsible preview
  setting?: string; // Scene location
  active_characters?: string[]; // Characters present in the scene
  raw_context?: string; // Raw context string
}

export interface ResponseSuggestion {
  text: string;
  type: string;
}
