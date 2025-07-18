"use client"

import { Button } from "@/components/ui/button"
import { PlusCircle, Loader2 } from "lucide-react"
import { SceneCard } from "@/components/scene-card"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import Link from "next/link"
import { useEffect, useState } from "react"
import { scenesApi } from "@/lib/api"
import type { Scene } from "@/lib/types"

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

  // Get character names from participants
  const characters = backendScene.participants 
    ? backendScene.participants.map((p: any) => p.character_name)
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
    title: backendScene.name || "Untitled Scene",
    lastPose,
    characters,
    status: backendScene.is_active ? "Ongoing" : "Completed",
    lastUpdated,
  }
}

export default function ScenesPage() {
  const [scenes, setScenes] = useState<Scene[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
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

    fetchScenes()
  }, [])

  if (error) {
    return (
      <div className="flex-1 p-4 md:p-8">
        <div className="mx-auto grid w-full max-w-4xl gap-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Your Scenes</h1>
              <p className="text-muted-foreground mt-1">Continue your stories or review completed narratives.</p>
            </div>
            <Button asChild>
              <Link href="/dashboard/scene-weaver">
                <PlusCircle className="mr-2 h-4 w-4" />
                Start New Scene
              </Link>
            </Button>
          </div>
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto grid w-full max-w-4xl gap-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Your Scenes</h1>
            <p className="text-muted-foreground mt-1">Continue your stories or review completed narratives.</p>
          </div>
          <Button asChild>
            <Link href="/dashboard/scene-weaver">
              <PlusCircle className="mr-2 h-4 w-4" />
              Start New Scene
            </Link>
          </Button>
        </div>
        
        {isLoading ? (
          <div className="grid gap-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="border rounded-lg p-6">
                <div className="flex items-center gap-4 mb-4">
                  <Skeleton className="h-6 w-48" />
                  <Skeleton className="h-6 w-20" />
                </div>
                <Skeleton className="h-4 w-32 mb-4" />
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            ))}
          </div>
        ) : scenes.length === 0 ? (
          <div className="text-center py-12">
            <h3 className="text-lg font-semibold mb-2">No scenes yet</h3>
            <p className="text-muted-foreground mb-4">
              Start your first scene to begin crafting your story.
            </p>
            <Button asChild>
              <Link href="/dashboard/scene-weaver">
                <PlusCircle className="mr-2 h-4 w-4" />
                Start New Scene
              </Link>
            </Button>
          </div>
        ) : (
          <div className="grid gap-6">
            {scenes.map((scene) => (
              <SceneCard key={scene.id} scene={scene} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
