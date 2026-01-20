/**
 * Types for continuity tracking
 */

export interface CharacterState {
    current_scene_id?: string;
    status: string;
    emotional_state?: string;
    active_bonds?: string[];
    [key: string]: any; // Allow flexibility for now
}
