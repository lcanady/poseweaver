export interface PlotThread {
  thread_id: string;
  thread_name: string;
  thread_description: string;
  thread_status: 'active' | 'resolved' | 'abandoned' | 'paused';
  importance: 'minor' | 'moderate' | 'major';
  created_timestamp: string;
  last_updated_timestamp: string;
  related_characters: Array<{
    character_id: string;
    character_name: string;
    relevance: 'primary' | 'secondary' | 'tertiary';
  }>;
  thread_elements: PlotThreadElement[];
  scenes: Array<{
    scene_id: string;
    scene_name: string;
    last_activity: string;
  }>;
  parent_thread_id?: string;
  child_thread_ids?: string[];
}

export interface PlotThreadElement {
  element_id: string;
  thread_id: string;
  element_type: 'event' | 'clue' | 'revelation' | 'decision' | 'consequence' | 'goal';
  element_name: string;
  element_description: string;
  timestamp: string;
  scene_id?: string;
  pose_id?: string;
  status: 'introduced' | 'developing' | 'resolved' | 'abandoned';
  related_characters: Array<{
    character_id: string;
    character_name: string;
    aware: boolean;
  }>;
}

export interface PlotThreadTrackingProps {
  scene_id?: string;
  threads: PlotThread[];
  onThreadClick?: (thread: PlotThread) => void;
  onElementClick?: (element: PlotThreadElement) => void;
  onCreateThread?: () => void;
  onUpdateThread?: (thread: PlotThread) => void;
  onDeleteThread?: (thread_id: string) => void;
  onCreateElement?: (thread_id: string) => void;
  onUpdateElement?: (element: PlotThreadElement) => void;
  onDeleteElement?: (element_id: string) => void;
  compact?: boolean;
  editable?: boolean;
}

export interface RelationshipDynamicsProps {
  scene_id?: string;
  character_relationships: Array<{
    relationship_id: string;
    character_id: string;
    character_name: string;
    related_character_id: string;
    related_character_name: string;
    relationship_type: string;
    dynamics: Array<{
      timestamp: string;
      trust_level: number;
      tension_level: number;
      description: string;
    }>;
  }>;
  onRelationshipClick?: (relationship_id: string) => void;
  compact?: boolean;
}
