/**
 * Types for continuity checking and management
 */

export interface ContinuityFlag {
  id: string;
  scene_id: string;
  pose_id?: string;
  character_id?: string;
  character_name?: string;
  flag_type: 'character_consistency' | 'environmental_contradiction' | 'timeline_error' | 'plot_hole' | 'relationship_inconsistency';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  suggestion?: string;
  confidence_score: number;
  created_at: string;
  updated_at: string;
  resolved: boolean;
  resolved_at?: string;
  resolved_by?: string;
  resolution_notes?: string;
  metadata?: {
    affected_characters?: string[];
    conflicting_details?: string[];
    reference_poses?: string[];
    context?: string;
  };
}

export interface ContinuityAnalysis {
  analysis_id: string;
  scene_id: string;
  character_id: string;
  character_name: string;
  pose_text: string;
  analysis_type: 'full' | 'character' | 'environment' | 'plot';
  timestamp: string;
  overall_score: number;
  flags: ContinuityFlag[];
  character_analysis?: CharacterConsistencyAnalysis;
  environment_analysis?: EnvironmentConsistencyAnalysis;
  plot_analysis?: PlotConsistencyAnalysis;
  suggestions?: string[];
  warnings?: ContinuityWarning[];
}

export interface CharacterConsistencyAnalysis {
  character_id: string;
  character_name: string;
  consistency_score: number;
  personality_consistency: number;
  voice_consistency: number;
  behavior_consistency: number;
  relationship_consistency: number;
  inconsistencies: {
    type: 'personality' | 'voice' | 'behavior' | 'relationship';
    description: string;
    severity: 'low' | 'medium' | 'high';
    suggestion?: string;
  }[];
  historical_patterns?: {
    speech_patterns: string[];
    behavior_patterns: string[];
    emotional_patterns: string[];
  };
}

export interface EnvironmentConsistencyAnalysis {
  environment_id: string;
  location_name: string;
  consistency_score: number;
  physical_consistency: number;
  atmospheric_consistency: number;
  temporal_consistency: number;
  inconsistencies: {
    type: 'physical' | 'atmospheric' | 'temporal' | 'lighting' | 'weather';
    description: string;
    severity: 'low' | 'medium' | 'high';
    suggestion?: string;
  }[];
  established_details: {
    physical_features: string[];
    atmospheric_elements: string[];
    temporal_markers: string[];
  };
}

export interface PlotConsistencyAnalysis {
  plot_threads: {
    thread_id: string;
    title: string;
    status: 'active' | 'resolved' | 'abandoned';
    consistency_score: number;
    last_referenced: string;
  }[];
  narrative_flow_score: number;
  pacing_analysis: {
    current_pace: 'slow' | 'moderate' | 'fast';
    recommended_pace: 'slow' | 'moderate' | 'fast';
    pacing_issues?: string[];
  };
}

export interface ContinuityWarning {
  id: string;
  type: 'character' | 'environment' | 'plot' | 'timeline';
  severity: 'info' | 'warning' | 'error';
  title: string;
  message: string;
  suggestion?: string;
  action_required: boolean;
  dismissible: boolean;
  auto_dismiss_after?: number; // seconds
}

export interface CharacterState {
  id: string;
  scene_id: string;
  character_id: string;
  character_name: string;
  current_location: string;
  physical_state: {
    health: string;
    injuries?: string[];
    equipment?: string[];
    appearance?: string;
  };
  emotional_state: {
    primary_emotion: string;
    secondary_emotions?: string[];
    mood?: string;
    stress_level?: number;
  };
  mental_state: {
    alertness?: string;
    focus?: string;
    memory_issues?: string[];
  };
  relationships: {
    character_name: string;
    relationship_type: string;
    relationship_status: string;
    last_interaction: string;
  }[];
  plot_knowledge: {
    known_facts: string[];
    secrets: string[];
    objectives: string[];
  };
  last_updated: string;
  updated_by: string;
  state_history: CharacterStateChange[];
}

export interface CharacterStateChange {
  id: string;
  timestamp: string;
  pose_id?: string;
  change_type: 'location' | 'physical' | 'emotional' | 'mental' | 'relationship' | 'knowledge';
  before_value: string;
  after_value: string;
  change_reason?: string;
  automatic: boolean;
}

export interface EnvironmentState {
  id: string;
  scene_id: string;
  location_name: string;
  location_type: string;
  physical_description: string;
  atmospheric_conditions: {
    lighting: string;
    weather?: string;
    temperature?: string;
    sounds?: string[];
    scents?: string[];
  };
  temporal_markers: {
    time_of_day: string;
    season?: string;
    special_events?: string[];
  };
  interactive_elements: {
    element_name: string;
    description: string;
    state: string;
    interactive: boolean;
  }[];
  occupants: string[];
  last_updated: string;
  environment_history: EnvironmentStateChange[];
}

export interface EnvironmentStateChange {
  id: string;
  timestamp: string;
  pose_id?: string;
  change_type: 'physical' | 'atmospheric' | 'temporal' | 'occupancy';
  description: string;
  before_state?: string;
  after_state: string;
  automatic: boolean;
}

export interface ContinuitySummary {
  scene_id: string;
  scene_name: string;
  overall_score: number;
  total_flags: number;
  unresolved_flags: number;
  flag_distribution: {
    character_consistency: number;
    environmental_contradiction: number;
    timeline_error: number;
    plot_hole: number;
    relationship_inconsistency: number;
  };
  severity_distribution: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  recent_activity: {
    new_flags_24h: number;
    resolved_flags_24h: number;
    analysis_count_24h: number;
  };
  recommendations: string[];
  last_updated: string;
}

export interface ContinuityDashboardProps {
  scene_id: string;
  scene_name: string;
  onFlagResolve?: (flagId: string, resolution: string) => void;
  onCharacterStateUpdate?: (characterId: string, updates: Partial<CharacterState>) => void;
  onEnvironmentStateUpdate?: (environmentId: string, updates: Partial<EnvironmentState>) => void;
  onAnalyzeContent?: (content: string, analysisType: string) => void;
  showRealTimeAlerts?: boolean;
  showFlagManagement?: boolean;
  showCharacterStates?: boolean;
  showEnvironmentStates?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export interface ContinuityAlertsProps {
  scene_id: string;
  warnings: ContinuityWarning[];
  onDismiss?: (warningId: string) => void;
  onAction?: (warningId: string, actionType: string) => void;
  maxVisible?: number;
  position?: 'top' | 'bottom' | 'fixed';
  autoHide?: boolean;
}

export interface ContinuityFlagManagerProps {
  scene_id: string;
  flags: ContinuityFlag[];
  onResolve?: (flagId: string, resolution: string) => void;
  onFilter?: (filters: ContinuityFlagFilters) => void;
  onSort?: (sortBy: string, sortOrder: 'asc' | 'desc') => void;
  showResolved?: boolean;
  showFilters?: boolean;
  showBulkActions?: boolean;
  paginate?: boolean;
  pageSize?: number;
}

export interface ContinuityFlagFilters {
  flag_type?: string[];
  severity?: string[];
  character_id?: string;
  resolved?: boolean;
  date_range?: {
    start: string;
    end: string;
  };
}

export interface CharacterStateDisplayProps {
  character_states: CharacterState[];
  scene_id: string;
  editable?: boolean;
  onStateUpdate?: (characterId: string, updates: Partial<CharacterState>) => void;
  onHistoryView?: (characterId: string) => void;
  showRelationships?: boolean;
  showPlotKnowledge?: boolean;
  showHistory?: boolean;
  compactView?: boolean;
}

export interface EnvironmentStateDisplayProps {
  environment_states: EnvironmentState[];
  scene_id: string;
  editable?: boolean;
  onStateUpdate?: (environmentId: string, updates: Partial<EnvironmentState>) => void;
  onHistoryView?: (environmentId: string) => void;
  showInteractiveElements?: boolean;
  showOccupants?: boolean;
  showHistory?: boolean;
  compactView?: boolean;
}

// API Response types
export interface ContinuityAnalysisResponse {
  success: boolean;
  data?: ContinuityAnalysis;
  message?: string;
  error?: string;
}

export interface ContinuityFlagsResponse {
  success: boolean;
  data?: ContinuityFlag[];
  meta?: {
    total_flags: number;
    unresolved_flags: number;
    resolved_flags: number;
    flag_type_distribution: Record<string, number>;
    severity_distribution: Record<string, number>;
    limit: number;
    skip: number;
    sort_field: string;
    sort_order: string;
    filters: ContinuityFlagFilters;
  };
  message?: string;
  error?: string;
}

export interface CharacterStatesResponse {
  success: boolean;
  data?: CharacterState[];
  meta?: {
    scene_id: string;
    total_characters: number;
    last_updated: string;
  };
  message?: string;
  error?: string;
}

export interface EnvironmentStatesResponse {
  success: boolean;
  data?: EnvironmentState[];
  meta?: {
    scene_id: string;
    current_location: string;
    last_updated: string;
  };
  message?: string;
  error?: string;
}

export interface ContinuitySummaryResponse {
  success: boolean;
  data?: ContinuitySummary;
  message?: string;
  error?: string;
} 