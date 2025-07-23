/**
 * Scene Poses Service
 * 
 * This service provides frontend access to the scene poses CRUD operations with debounce.
 * All state-changing operations (add, edit, delete) are debounced for 1s before saving.
 */

import axios from 'axios';

interface CreatePoseRequest {
  character_name: string;
  content: string;
  pose_type?: string;
  is_ooc?: boolean;
  analysis_data?: Record<string, any>;
}

interface UpdatePoseRequest {
  content?: string;
  pose_type?: string;
  is_ooc?: boolean;
  analysis_data?: Record<string, any>;
}

interface PoseResponse {
  id: string;
  scene_id: string;
  character_name: string;
  content: string;
  pose_type: string;
  is_ooc: boolean;
  timestamp: string;
  analysis_data?: Record<string, any>;
  word_count?: number;
}

/**
 * Scene poses service with debounced operations
 */
export const scenePosesService = {
  /**
   * Create a new pose in a scene
   * The operation is debounced on the backend for 1 second
   */
  createPose: async (sceneId: string, poseData: CreatePoseRequest): Promise<string> => {
    try {
      const response = await axios.post(
        `/api/scenes/${sceneId}/poses`, 
        poseData
      );
      return response.data.id;
    } catch (error) {
      console.error('Error creating pose:', error);
      throw error;
    }
  },

  /**
   * Get poses from a scene
   */
  getPoses: async (sceneId: string, limit = 100, includeOoc = true): Promise<PoseResponse[]> => {
    try {
      const response = await axios.get(
        `/api/scenes/${sceneId}/poses`, 
        { params: { limit, include_ooc: includeOoc } }
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching poses:', error);
      throw error;
    }
  },

  /**
   * Update an existing pose
   * The operation is debounced on the backend for 1 second
   */
  updatePose: async (sceneId: string, poseId: string, poseData: UpdatePoseRequest): Promise<void> => {
    try {
      await axios.put(
        `/api/scenes/${sceneId}/poses/${poseId}`, 
        poseData
      );
    } catch (error) {
      console.error('Error updating pose:', error);
      throw error;
    }
  },

  /**
   * Delete a pose from a scene
   * The operation is debounced on the backend for 1 second
   */
  deletePose: async (sceneId: string, poseId: string): Promise<void> => {
    try {
      await axios.delete(
        `/api/scenes/${sceneId}/poses/${poseId}`
      );
    } catch (error) {
      console.error('Error deleting pose:', error);
      throw error;
    }
  }
};
