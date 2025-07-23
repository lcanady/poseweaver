/**
 * Types for scene management and timeline visualization
 */

export interface Scene {
  id: string;
  name: string;
  title?: string; // For backward compatibility
  description: string;
  created_at: string;
  updated_at: string;
  created_by: string;
  is_active: boolean;
  status: 'Ongoing' | 'Completed' | 'Archived';
  participants: SceneParticipant[];
  poses: ScenePose[];
  tags?: string[];
  lastPose?: string; // For display purposes
  lastUpdated?: string; // For display purposes
  characters?: string[]; // For backward compatibility
  pose_count?: number;
  summary?: SceneSummary;
  metadata?: {
    total_words?: number;
    average_pose_length?: number;
    most_active_character?: string;
    scene_duration?: string;
  };
}

export interface SceneParticipant {
  character_id: string;
  character_name: string;
  joined_at: string;
  pose_count: number;
  last_pose_at?: string;
  is_active: boolean;
}

export interface ScenePose {
  id: string;
  character_id: string;
  character_name: string;
  pose_text: string;
  enhanced_text?: string;
  pose_type: 'action' | 'dialogue' | 'internal' | 'ooc' | 'mixed';
  timestamp: string;
  tags?: string[];
  is_ooc: boolean;
  word_count?: number;
  analysis?: {
    sentiment?: string;
    emotional_tone?: string;
    plot_significance?: number;
    character_development?: string[];
  };
}

export interface SceneSummary {
  id: string;
  scene_id: string;
  summary_text: string;
  summary_type: 'comprehensive' | 'character' | 'plot' | 'environment' | 'catchup';
  generated_at: string;
  metadata: {
    scene_name: string;
    pose_count: number;
    character_count: number;
    word_count?: number;
    key_events?: string[];
    character_focus?: string;
  };
  is_editable: boolean;
  edited_at?: string;
  edited_by?: string;
}

export interface SceneSearchFilters {
  query?: string;
  active?: boolean;
  start_date?: string;
  end_date?: string;
  participants?: string[];
  tags?: string[];
  status?: 'active' | 'completed' | 'archived';
  sort_by?: 'relevance' | 'created_at' | 'updated_at' | 'name';
  sort_order?: 'asc' | 'desc';
  limit?: number;
  skip?: number;
}

export interface PoseSearchFilters {
  query?: string;
  scene_id?: string;
  character_id?: string;
  pose_type?: string;
  start_date?: string;
  end_date?: string;
  tags?: string[];
  include_ooc?: boolean;
  min_word_count?: number;
  sentiment?: string;
  limit?: number;
  skip?: number;
}

export interface TimelineEvent {
  id: string;
  type: 'pose' | 'character_join' | 'character_leave' | 'scene_start' | 'scene_end' | 'summary_generated';
  timestamp: string;
  title: string;
  description: string;
  character_name?: string;
  character_id?: string;
  pose_text?: string;
  pose_type?: string;
  tags?: string[];
  metadata?: {
    word_count?: number;
    is_ooc?: boolean;
    sentiment?: string;
    plot_significance?: number;
  };
}

export interface SceneCreationData {
  name: string;
  description: string;
  tags?: string[];
  participants?: {
    character_id: string;
    character_name: string;
  }[];
  initial_setting?: string;
  scene_type?: 'oneshot' | 'ongoing' | 'campaign';
  privacy_level?: 'private' | 'shared' | 'public';
  allow_new_participants?: boolean;
}

export interface SceneManagementOptions {
  allow_editing: boolean;
  allow_archiving: boolean;
  allow_deletion: boolean;
  allow_participant_management: boolean;
  allow_summary_generation: boolean;
  allow_export: boolean;
  show_analytics: boolean;
  show_timeline: boolean;
  show_search: boolean;
}

export interface SceneAnalytics {
  total_poses: number;
  total_words: number;
  unique_characters: number;
  active_days: number;
  average_poses_per_day: number;
  most_active_character: {
    name: string;
    pose_count: number;
    percentage: number;
  };
  pose_type_distribution: {
    action: number;
    dialogue: number;
    internal: number;
    ooc: number;
    mixed: number;
  };
  activity_timeline: {
    date: string;
    pose_count: number;
    word_count: number;
  }[];
  character_activity: {
    character_name: string;
    pose_count: number;
    word_count: number;
    last_active: string;
  }[];
  sentiment_analysis?: {
    positive: number;
    negative: number;
    neutral: number;
  };
}

export interface SceneExportOptions {
  format: 'json' | 'csv' | 'txt' | 'html';
  include_poses: boolean;
  include_metadata: boolean;
  include_summaries: boolean;
  include_analytics: boolean;
  date_range?: {
    start: string;
    end: string;
  };
  character_filter?: string[];
  pose_type_filter?: string[];
}

export interface SceneSearchResult {
  item_id: string;
  item_type: 'scene' | 'pose' | 'character';
  content_preview: string;
  relevance_score: number;
  timestamp: string;
  metadata: {
    scene_name?: string;
    character_name?: string;
    pose_type?: string;
    tags?: string[];
    word_count?: number;
  };
}

export interface SceneValidationError {
  field: string;
  message: string;
  code: 'required' | 'invalid' | 'too_long' | 'too_short' | 'duplicate';
}

export interface SceneFormState {
  data: SceneCreationData;
  errors: SceneValidationError[];
  isSubmitting: boolean;
  isDirty: boolean;
  isValid: boolean;
}

// API Response types
export interface SceneApiResponse {
  success: boolean;
  data?: Scene;
  message?: string;
  error?: string;
}

export interface SceneListApiResponse {
  success: boolean;
  data?: Scene[];
  meta?: {
    total: number;
    limit: number;
    skip: number;
    has_more: boolean;
  };
  message?: string;
  error?: string;
}

export interface SceneSearchApiResponse {
  success: boolean;
  data?: SceneSearchResult[];
  meta?: {
    query: string;
    total_results: number;
    limit: number;
    skip: number;
    filters: SceneSearchFilters;
  };
  message?: string;
  error?: string;
}

export interface SceneSummaryApiResponse {
  success: boolean;
  data?: SceneSummary;
  message?: string;
  error?: string;
}

export interface SceneAnalyticsApiResponse {
  success: boolean;
  data?: SceneAnalytics;
  message?: string;
  error?: string;
}

// Component props interfaces
export interface SceneCardProps {
  scene: Scene;
  onEdit?: (scene: Scene) => void;
  onArchive?: (sceneId: string) => void;
  onDelete?: (sceneId: string) => void;
  onViewHistory?: (sceneId: string) => void;
  onGenerateSummary?: (sceneId: string) => void;
  showActions?: boolean;
  showAnalytics?: boolean;
}

export interface SceneTimelineProps {
  scene: Scene;
  events: TimelineEvent[];
  onPoseClick?: (poseId: string) => void;
  onCharacterClick?: (characterId: string) => void;
  showFilters?: boolean;
  showSearch?: boolean;
  groupByDate?: boolean;
  highlightCharacter?: string;
}

export interface SceneSearchProps {
  initialFilters?: SceneSearchFilters;
  onSearchResults?: (results: SceneSearchResult[]) => void;
  onFilterChange?: (filters: SceneSearchFilters) => void;
  showAdvancedFilters?: boolean;
  showExportOptions?: boolean;
  placeholder?: string;
  maxResults?: number;
}

export interface SceneSummaryProps {
  summary: SceneSummary;
  onEdit?: (summaryId: string, newText: string) => void;
  onRegenerate?: (sceneId: string, options: SummaryGenerationOptions) => void;
  onExport?: (summary: SceneSummary) => void;
  editable?: boolean;
  showMetadata?: boolean;
  showRegenerateOptions?: boolean;
}

export interface SummaryGenerationOptions {
  focus: 'comprehensive' | 'character' | 'plot' | 'environment';
  character_id?: string;
  max_length: number;
  include_details: boolean;
  formal_style: boolean;
  chronological: boolean;
  highlight_key_events: boolean;
}

export interface SceneManagementDashboardProps {
  scenes: Scene[];
  onSceneCreate?: (sceneData: SceneCreationData) => void;
  onSceneEdit?: (sceneId: string, sceneData: Partial<SceneCreationData>) => void;
  onSceneArchive?: (sceneId: string) => void;
  onSceneDelete?: (sceneId: string) => void;
  onSceneExport?: (sceneId: string, options: SceneExportOptions) => void;
  options?: SceneManagementOptions;
  loading?: boolean;
  error?: string;
} 