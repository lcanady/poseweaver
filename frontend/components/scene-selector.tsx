"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { useToast } from "@/hooks/use-toast"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Loader2, FolderOpen } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { getApiUrl } from '@/utils/api-utils';

// Define the Scene type
interface Scene {
  _id: string
  name: string
  created_by: string
  created_at: string
  updated_at?: string
  description?: string
}

interface SceneSelectorProps {
  onSceneSelected: (sceneId: string, title: string, context: any, characterId: string) => void
}

export function SceneSelector({ onSceneSelected }: SceneSelectorProps) {
  const [scenes, setScenes] = useState<Scene[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const { toast } = useToast()
  const { getToken } = useAuth()

  // Fetch saved scenes when dialog is opened
  useEffect(() => {
    if (open) {
      fetchSavedScenes()
    }
  }, [open])

  const fetchSavedScenes = async () => {
    setIsLoading(true)
    try {
      const token = await getToken()
      if (!token) throw new Error("No authentication token")

      const scenesUrl = `${getApiUrl()}/api/scenes?limit=50&sort=updated_at&order=desc`

      const response = await fetch(scenesUrl, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch scenes: ${response.status}`)
      }

      const data = await response.json()

      if (data.success && data.data) {
        console.log(`Loaded ${data.data.length} scenes for scene selector`);
        setScenes(data.data)
      } else {
        toast({
          title: "Error",
          description: "Failed to load saved scenes",
          variant: "destructive",
        })
      }
    } catch (error) {
      console.error('Error fetching scenes:', error)
      toast({
        title: "Error",
        description: "Failed to load saved scenes",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSceneSelect = async (sceneId: string, title: string) => {
    try {
      const token = await getToken()
      if (!token) throw new Error("No authentication token")

      // Fetch the full scene data
      const sceneUrl = `${getApiUrl()}/api/scenes/${sceneId}`

      const response = await fetch(sceneUrl, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) throw new Error("Failed to load scene data")

      const data = await response.json()

      if (data.success && data.data) {
        // Extract scene context, character ID, and title from the fetched data
        const { context, character_id, name } = data.data

        // Use the title from the fetched data to ensure it's current
        const sceneTitle = name || title

        // Call the parent component's callback with scene data
        onSceneSelected(sceneId, sceneTitle, context || {}, character_id || "")
        setOpen(false)

        toast({
          title: "Scene Loaded",
          description: `"${sceneTitle}" has been loaded successfully.`,
        })

        // Trigger refresh of recent scenes to update "last updated" times
        localStorage.setItem('sceneUpdated', 'true');
        // Trigger storage event for same-tab updates
        window.dispatchEvent(new StorageEvent('storage', {
          key: 'sceneUpdated',
          newValue: 'true',
          storageArea: localStorage
        }));
      } else {
        throw new Error("Failed to load scene data")
      }
    } catch (error) {
      console.error('Error loading scene:', error)
      toast({
        title: "Error",
        description: "Failed to load scene data",
        variant: "destructive",
      })
    }
  }

  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString() + " " + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <FolderOpen className="mr-2 h-4 w-4" />
          Load Saved Scene
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Your Saved Scenes</DialogTitle>
          <DialogDescription>
            Select a saved scene to continue working on it.
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="h-[300px] mt-4 rounded-md border p-2">
          {isLoading ? (
            <div className="flex justify-center items-center h-full">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : scenes.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              No saved scenes found.
            </div>
          ) : (
            <div className="space-y-2">
              {scenes.map((scene) => (
                <div
                  key={scene._id}
                  className="p-3 rounded-md border hover:bg-accent cursor-pointer transition-colors"
                  onClick={() => handleSceneSelect(scene._id, scene.name)}
                >
                  <div className="font-medium">{scene.name}</div>
                  <div className="text-sm text-muted-foreground">
                    Last updated: {formatDate(scene.updated_at || scene.created_at)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
