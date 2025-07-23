"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScenePosesList } from './scene-poses-list'
import { FolderOpen } from 'lucide-react'

interface SceneContextProps {
  sceneId?: string;
  onSceneLoad?: (sceneId: string) => void;
}

export function SceneContext({ sceneId: initialSceneId, onSceneLoad }: SceneContextProps) {
  const [sceneId, setSceneId] = useState<string | undefined>(initialSceneId);
  const [sceneTitle, setSceneTitle] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load scene data if scene ID is provided
  useEffect(() => {
    if (sceneId) {
      loadSceneData();
    }
  }, [sceneId]);

  // Function to load scene data
  const loadSceneData = async () => {
    if (!sceneId) return;
    
    try {
      setLoading(true);
      setError(null);
      
      // Fetch scene data from API
      // This is a placeholder - you would actually call your scene API
      const response = await fetch(`/api/scenes/${sceneId}`);
      const sceneData = await response.json();
      
      setSceneTitle(sceneData.name || "Untitled Scene");
    } catch (err) {
      setError('Failed to load scene data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Handle scene title change
  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSceneTitle(e.target.value);
  };

  // Function to load a saved scene
  const handleLoadScene = async () => {
    // This would typically open a scene selection dialog
    // For now, let's simulate loading a scene
    if (onSceneLoad) {
      // This is a placeholder scene ID
      const selectedSceneId = "scene_123456";
      setSceneId(selectedSceneId);
      onSceneLoad(selectedSceneId);
    }
  };

  // Handle scene update
  const handleSceneUpdate = () => {
    // This would typically save scene data like the title
    console.log("Scene updated");
  };

  // Handle successful pose operation
  const handlePoseUpdateSuccess = () => {
    // You might want to refresh certain data after a pose is added, edited or deleted
    console.log("Pose operation successful");
  };

  return (
    <div className="space-y-4">
      <Card className="w-full">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg font-medium">Scene Context</CardTitle>
          <p className="text-sm text-muted-foreground">
            The ongoing narrative and previous posts.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <label className="text-sm font-medium" htmlFor="scene-title">
                Scene Title
              </label>
              <Input
                id="scene-title"
                placeholder="Enter scene title"
                value={sceneTitle}
                onChange={handleTitleChange}
                className="mt-1"
              />
            </div>
            <div className="ml-4">
              <Button
                variant="outline"
                className="flex items-center gap-2"
                onClick={handleLoadScene}
              >
                <FolderOpen className="h-4 w-4" />
                Load Saved Scene
              </Button>
            </div>
          </div>
          
          {error && (
            <div className="bg-destructive/20 text-destructive p-3 rounded-md">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Scene Poses List with CRUD operations */}
      {sceneId ? (
        <ScenePosesList 
          sceneId={sceneId}
          onUpdateSuccess={handlePoseUpdateSuccess}
        />
      ) : (
        <Card className="w-full">
          <CardContent className="py-8">
            <div className="text-center text-muted-foreground">
              <p>No scene loaded. Please load a scene to view and manage poses.</p>
              <Button
                variant="outline"
                className="mt-4 flex items-center gap-2 mx-auto"
                onClick={handleLoadScene}
              >
                <FolderOpen className="h-4 w-4" />
                Load Scene
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {sceneId && (
        <div className="flex justify-end">
          <Button onClick={handleSceneUpdate}>
            Update Scene
          </Button>
        </div>
      )}
    </div>
  );
}
