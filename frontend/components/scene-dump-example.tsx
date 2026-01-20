"use client"

import { StandaloneSceneDumpProcessor } from './standalone-scene-dump-processor'
import { type ProcessedPose } from '@/hooks/useSceneDumpProcessor'

interface SceneDumpExampleProps {
  // Pass these props from your parent component/page
  openrouterApiKey: string
  currentUser: {
    id: string
    display_name: string
  }
  currentScene?: {
    id: string
    name: string
  }
}

export function SceneDumpExample({ openrouterApiKey, currentUser, currentScene }: SceneDumpExampleProps) {
  // Optional: Save poses to your backend
  const handleSaveToScene = async (poses: ProcessedPose[], sceneId: string): Promise<boolean> => {
    try {
      const token = localStorage.getItem('access_token')

      // Call your backend API to save poses
      const response = await fetch(`/api/scenes/${sceneId}/poses/bulk`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          poses: poses.map(pose => ({
            character_name: pose.character_name,
            pose_text: pose.enhanced_text || pose.pose_text,
            pose_type: pose.pose_type,
            timestamp: pose.timestamp,
            mentions: pose.mentions
          }))
        })
      })

      return response.ok
    } catch (error) {
      console.error('Failed to save poses:', error)
      return false
    }
  }

  // Optional: Handle processing completion
  const handleProcessingComplete = (result: any) => {
    if (result.success) {
      console.log(`Successfully processed ${result.poses.length} poses!`)
    } else {
      console.error('Processing failed:', result.error)
    }
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Scene Dump Processor</h1>

      {!openrouterApiKey && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-4 mb-4">
          <h3 className="font-medium text-yellow-800">Missing OpenRouter API Key</h3>
          <p className="text-yellow-700">Please provide a OpenRouter.ai API key to enable processing.</p>
        </div>
      )}

      <StandaloneSceneDumpProcessor
        openrouterApiKey={openrouterApiKey}
        userId={currentUser.id}
        userDisplayName={currentUser.display_name}
        sceneId={currentScene?.id}
        sceneTitle={currentScene?.name}
        onProcessingComplete={handleProcessingComplete}
        onSaveToScene={currentScene ? handleSaveToScene : undefined}
      />
    </div>
  )
} 