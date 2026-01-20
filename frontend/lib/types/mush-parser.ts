export enum PoseType {
  ACTION = 'action',
  DIALOGUE = 'dialogue',
  MIXED = 'mixed',
  NARRATIVE = 'narrative',
  INTERNAL = 'internal',
}

export interface ParsedPose {
  character_name: string;
  content: string;
  pose_type: PoseType;
  is_ooc: boolean;
  timestamp?: string | null;
}

export interface ParsedScene {
  poses: ParsedPose[];
  room_description: string | null;
  characters_present: string[] | null;
  your_character: string | null;
}
