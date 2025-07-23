import { CharacterState } from './continuity';

export interface CharacterTimelineEntry {
  timestamp: string;
  character_id: string;
  character_name: string;
  state_snapshot: CharacterState;
  pose_id?: string;
  pose_snippet?: string;
  scene_id: string;
}

export interface CharacterRelationship {
  relationship_id: string;
  character_id: string;
  character_name: string;
  related_character_id: string;
  related_character_name: string;
  relationship_type: string;
  relationship_status: string;
  relationship_dynamics: string;
  trust_level: number; // 1-10
  familiarity: number; // 1-10
  last_interaction_timestamp: string;
  notable_interactions: Array<{
    timestamp: string;
    description: string;
    scene_id?: string;
    pose_id?: string;
  }>;
}

export interface CharacterTimelineViewProps {
  character_id?: string;
  scene_id?: string;
  timelineEntries: CharacterTimelineEntry[];
  onEntryClick?: (entry: CharacterTimelineEntry) => void;
  onPoseView?: (pose_id: string) => void;
  showPoseSnippets?: boolean;
  compact?: boolean;
  maxEntries?: number;
}

export interface CharacterRelationshipViewProps {
  character_id: string;
  character_name: string;
  relationships: CharacterRelationship[];
  onRelationshipClick?: (relationship: CharacterRelationship) => void;
  onCharacterClick?: (character_id: string) => void;
  compact?: boolean;
}

export interface CharacterConsistencyScoreProps {
  character_id: string;
  character_name: string;
  consistency_score: number; // 1-100
  recent_inconsistencies: Array<{
    timestamp: string;
    description: string;
    severity: 'low' | 'medium' | 'high';
    pose_id?: string;
    resolved: boolean;
  }>;
  onInconsistencyClick?: (inconsistency: any) => void;
}
