"use client"

import { useEffect, useState } from "react"
import { SceneManagementDashboard } from "@/components/scene-management/scene-management-dashboard"
import { scenesApi } from "@/lib/api"
import type { Scene, SceneCreationData, SceneExportOptions } from "@/types/scene"

// Helper function to format relative time
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
  
  if (diffInSeconds < 60) return "Just now"
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`
  if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)} days ago`
  if (diffInSeconds < 31536000) return `${Math.floor(diffInSeconds / 2592000)} months ago`
  return `${Math.floor(diffInSeconds / 31536000)} years ago`
}

// Transform backend scene data to frontend Scene type
function transformSceneData(backendScene: any): Scene | null {
  // Debug: log the backend scene data to see what fields are available
  console.log('Backend scene data:', backendScene)
  
  // Get the most recent pose text
  let lastPose = "No poses yet"
  if (backendScene.poses && backendScene.poses.length > 0) {
    const mostRecentPose = backendScene.poses[backendScene.poses.length - 1]
    if (mostRecentPose && mostRecentPose.pose_text) {
      lastPose = mostRecentPose.pose_text.length > 150 
        ? mostRecentPose.pose_text.substring(0, 150) + "..."
        : mostRecentPose.pose_text
    }
  }

  // Get character names from participants - support both old and new formats
  const participants = backendScene.participants 
    ? backendScene.participants.map((p: any) => ({
        character_id: p.character_id || p.id || '',
        character_name: p.character_name || p.name || '',
        joined_at: p.joined_at || backendScene.created_at,
        pose_count: p.pose_count || 0,
        last_pose_at: p.last_pose_at,
        is_active: p.is_active !== undefined ? p.is_active : true
      }))
    : []

  // Transform poses to new format
  const poses = backendScene.poses 
    ? backendScene.poses.map((pose: any) => ({
        id: pose.id || pose._id || '',
        character_id: pose.character_id || '',
        character_name: pose.character_name || '',
        pose_text: pose.pose_text || pose.content || '',
        enhanced_text: pose.enhanced_text,
        pose_type: pose.pose_type || 'mixed',
        timestamp: pose.timestamp || pose.created_at || new Date().toISOString(),
        tags: pose.tags || [],
        is_ooc: pose.is_ooc || false,
        word_count: pose.word_count || (pose.pose_text || '').split(/\s+/).length
      }))
    : []

  // Format the updated_at timestamp with relative time
  const lastUpdated = backendScene.updated_at 
    ? formatRelativeTime(backendScene.updated_at)
    : "Unknown"

  // Ensure ID is a string
  const sceneId = backendScene.id || backendScene._id
  if (!sceneId) {
    console.warn('Scene missing ID:', backendScene)
    return null // Skip scenes without IDs
  }
  const id = typeof sceneId === 'string' ? sceneId : String(sceneId)
  
  return {
    id,
    name: backendScene.name || "Untitled Scene",
    title: backendScene.name || "Untitled Scene", // For backward compatibility
    description: backendScene.description || "",
    created_at: backendScene.created_at || new Date().toISOString(),
    updated_at: backendScene.updated_at || new Date().toISOString(),
    created_by: backendScene.created_by || "",
    is_active: backendScene.is_active !== undefined ? backendScene.is_active : true,
    status: backendScene.is_active ? "Ongoing" : "Completed",
    participants,
    poses,
    tags: backendScene.tags || [],
    lastPose, // For backward compatibility
    lastUpdated, // For backward compatibility
    characters: participants.map(p => p.character_name), // For backward compatibility
    pose_count: poses.length,
    metadata: {
      total_words: poses.reduce((sum, p) => sum + (p.word_count || 0), 0),
      average_pose_length: poses.length > 0 ? poses.reduce((sum, p) => sum + (p.word_count || 0), 0) / poses.length : 0,
      most_active_character: participants.length > 0 ? participants.reduce((prev, current) => 
        (prev.pose_count > current.pose_count) ? prev : current
      ).character_name : undefined,
      scene_duration: backendScene.created_at ? 
        Math.floor((new Date().getTime() - new Date(backendScene.created_at).getTime()) / (1000 * 60 * 60 * 24)) + " days" : 
        undefined
    }
  }
}

export default function ScenesPage() {
  const [scenes, setScenes] = useState<Scene[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchScenes()
  }, [])

  const fetchScenes = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      const response = await scenesApi.getScenes()
      
      if (response.success && response.data) {
        const transformedScenes = response.data.map(transformSceneData).filter(Boolean) as Scene[]
        setScenes(transformedScenes)
      } else {
        setError('Failed to load scenes')
      }
    } catch (err) {
      console.error('Error fetching scenes:', err)
      setError('Failed to load scenes. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSceneCreate = async (data: SceneCreationData) => {
    try {
      const response = await scenesApi.createScene(data)
      
      if (response.success) {
        // Refresh scenes list
        fetchScenes()
      } else {
        throw new Error(response.error || 'Failed to create scene')
      }
    } catch (error) {
      console.error('Error creating scene:', error)
      throw error
    }
  }

  const handleSceneEdit = async (sceneId: string, data: Partial<SceneCreationData>) => {
    try {
      const response = await scenesApi.updateScene(sceneId, data)
      
      if (response.success) {
        // Refresh scenes list
        fetchScenes()
      } else {
        throw new Error(response.error || 'Failed to update scene')
      }
    } catch (error) {
      console.error('Error updating scene:', error)
      throw error
    }
  }

  const handleSceneArchive = async (sceneId: string) => {
    try {
      const response = await scenesApi.archiveScene(sceneId)
      
      if (response.success) {
        // Refresh scenes list
        fetchScenes()
      } else {
        throw new Error(response.error || 'Failed to archive scene')
      }
    } catch (error) {
      console.error('Error archiving scene:', error)
      throw error
    }
  }

  const handleSceneDelete = async (sceneId: string) => {
    try {
      const response = await scenesApi.deleteScene(sceneId)
      
      if (response.success) {
        // Refresh scenes list
        fetchScenes()
      } else {
        throw new Error(response.error || 'Failed to delete scene')
      }
    } catch (error) {
      console.error('Error deleting scene:', error)
      throw error
    }
  }

  const handleSceneExport = async (sceneId: string, options: SceneExportOptions) => {
    try {
      const response = await fetch(`/api/search-summary/export/scenes/${sceneId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to export scene')
      }

      // Handle different response types based on format
      if (options.format === 'json') {
        const data = await response.json()
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `scene-${sceneId}.json`
        a.click()
        URL.revokeObjectURL(url)
      } else {
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `scene-${sceneId}.${options.format}`
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Error exporting scene:', error)
      throw error
    }
  }

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto w-full max-w-7xl">
        <SceneManagementDashboard
          scenes={scenes}
          onSceneCreate={handleSceneCreate}
          onSceneEdit={handleSceneEdit}
          onSceneArchive={handleSceneArchive}
          onSceneDelete={handleSceneDelete}
          onSceneExport={handleSceneExport}
          options={{
            allow_editing: true,
            allow_archiving: true,
            allow_deletion: true,
            allow_participant_management: true,
            allow_summary_generation: true,
            allow_export: true,
            show_analytics: true,
            show_timeline: true,
            show_search: true
          }}
          loading={isLoading}
          error={error}
        />
      </div>
    </div>
  )
}
