"use client"

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ArrowUpRight } from "lucide-react"
import Link from "next/link"
import { useEffect, useState } from "react"
import { useAuth } from "@/contexts/auth-context"
import { formatDistanceToNow } from "date-fns"
import { getApiUrl } from '@/utils/api-utils';

// Define the Scene type
interface Scene {
  _id: string
  name: string
  status: "Ongoing" | "Completed"
  updated_at: string
  created_at: string
  description?: string
}

export function RecentScenes({ onDataLoaded }: { onDataLoaded?: (hasData: boolean) => void } = {}) {
  const [scenes, setScenes] = useState<Scene[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { getToken } = useAuth()

  const fetchScenes = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const token = await getToken();

      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${getApiUrl()}/api/scenes?limit=10&sort=updated_at&order=desc`, {
        headers
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch scenes: ${response.status}`);
      }

      const data = await response.json();

      if (data.success && data.data) {
        // Sort scenes by updated_at to ensure most recent first
        const sortedScenes = data.data.sort((a: Scene, b: Scene) => {
          const aTime = new Date(a.updated_at || a.created_at).getTime();
          const bTime = new Date(b.updated_at || b.created_at).getTime();
          return bTime - aTime; // Most recent first
        });

        // Take only the first 3 most recent scenes for display
        setScenes(sortedScenes.slice(0, 3))
        // Notify parent component about data status
        if (onDataLoaded) {
          onDataLoaded(sortedScenes.length > 0)
        }
      } else {
        setError(data.message || 'Failed to fetch scenes')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchScenes()
  }, [getToken]) // Add getToken to dependency array

  // Listen for scene updates via localStorage events
  useEffect(() => {
    const handleSceneUpdate = (event: StorageEvent) => {
      if (event.key === 'sceneUpdated') {
        console.log('Scene updated, refreshing recent scenes...');
        fetchScenes();
        // Clear the event flag
        localStorage.removeItem('sceneUpdated');
      }
    };

    const handleFocusReturn = () => {
      // Check if scenes were updated while user was away
      const wasUpdated = localStorage.getItem('sceneUpdated');
      if (wasUpdated) {
        console.log('Scene was updated while away, refreshing recent scenes...');
        fetchScenes();
        localStorage.removeItem('sceneUpdated');
      }
    };

    window.addEventListener('storage', handleSceneUpdate);
    window.addEventListener('focus', handleFocusReturn);

    return () => {
      window.removeEventListener('storage', handleSceneUpdate);
      window.removeEventListener('focus', handleFocusReturn);
    };
  }, []);
  return (
    <Card>
      <CardHeader className="flex flex-row items-center">
        <div className="grid gap-2">
          <CardTitle>Recent Scenes</CardTitle>
          <CardDescription>Jump back into your ongoing narratives.</CardDescription>
        </div>
        <Button asChild size="sm" className="ml-auto gap-1">
          <Link href="/dashboard/scenes">
            View All Scenes
            <ArrowUpRight className="h-4 w-4" />
          </Link>
        </Button>
      </CardHeader>
      <CardContent className="grid gap-6">
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading scenes...</p>
        ) : error ? (
          <p className="text-sm text-red-500">{error}</p>
        ) : scenes.length === 0 ? (
          <p className="text-sm text-muted-foreground">No scenes found. Create your first scene!</p>
        ) : (
          scenes.map((scene) => (
            <div key={scene._id} className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-medium leading-none">{scene.name}</p>
                <p className="text-sm text-muted-foreground">
                  Last updated {formatDistanceToNow(new Date(scene.updated_at), { addSuffix: true })}
                </p>
              </div>
              <div className="flex items-center gap-4">
                <Badge variant={scene.status === "Ongoing" ? "default" : "outline"}>
                  {scene.status || "Ongoing"}
                </Badge>
                {(scene.status === "Ongoing" || !scene.status) && (
                  <Button asChild variant="outline" size="sm">
                    <Link href={`/dashboard/scene-weaver?scene=${scene._id}`}>Continue</Link>
                  </Button>
                )}
              </div>
            </div>
          ))
        )}

      </CardContent>
    </Card>
  )
}
