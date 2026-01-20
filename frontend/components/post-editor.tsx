"use client"

import { useState, useEffect, Fragment } from "react"
import { useDebounce } from "@uidotdev/usehooks"
import type { PoseContext, ResponseSuggestion, Pose } from "@/types/context"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Wand2, Loader2, Copy, Sparkles, Save, ChevronDown, ChevronUp, MessageSquareQuote, GripVertical, X, Plus, Settings } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { SceneAnalysis } from "@/components/scene-analysis"
import { SceneSelector } from "@/components/scene-selector"
import { SceneDumpProcessor } from "@/components/scene-dump-processor"
import { cn } from "@/lib/utils"
import { Skeleton } from "@/components/ui/skeleton"
import type { SceneDumpProcessingResult } from "@/hooks/useSceneDumpProcessor"
import { getApiUrl } from '@/utils/api-utils';
import { useAuth } from "@/contexts/auth-context"

// Initialize with empty strings instead of placeholder text
const initialScene = ``
const initialPost = ``



// API function to enhance a pose
// API function to enhance a pose
async function enhancePose(originalPose: string, sceneContext: any, characterData: any, enhancementStyle: string, token: string, includeEnvironmentalDetails: boolean = false) {
  try {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };

    const response = await fetch(`${getApiUrl()}/api/pose/enhance`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        original_pose: originalPose,
        character: characterData,
        context: sceneContext,
        enhancement_style: enhancementStyle,
        include_environmental_details: includeEnvironmentalDetails,
        instructions: includeEnvironmentalDetails ?
          "IMPORTANT: You MUST heavily incorporate the provided scene context into your enhancement. Reference key locations, atmospheres, and other characters mentioned in the scene context. Make your enhancement directly relevant to the specific scene described. You may include environmental details and sensory descriptions. Preserve any Discord-style formatting from the original pose, including indentation, paragraph structure, and message breaks." :
          "IMPORTANT: You MUST heavily incorporate the provided scene context into your enhancement. Reference key locations, atmospheres, and other characters mentioned in the scene context. Make your enhancement directly relevant to the specific scene described. DO NOT add ANY environmental details, ambient descriptions, sensory perceptions, or atmospheric elements that weren't in the original post. Focus ONLY on enhancing character actions and explicit movements. Do not describe smells, sounds, feelings, or ambient environment that weren't in the original. Preserve all Discord-style formatting including indentation at paragraph beginnings, spacing between paragraphs, timestamps, usernames, and message structure."
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to enhance pose');
    }

    return await response.json();
  } catch (error) {
    console.error('Error enhancing pose:', error);
    throw error;
  }
}

// Default characters as fallback
const defaultCharacters = [
  { id: "jax", name: "Jax, the Cyber-Noir Detective" },
  { id: "elara", name: "Elara, the Elven Diplomat" },
  { id: "grak", name: "Grak, the Orc Barbarian" },
]

// CollapsiblePose component for displaying poses with drag and drop
function CollapsiblePose({
  pose,
  index,
  onDelete,
  onDragStart,
  onDragOver,
  onDrop,
  onDragEnd,
  isDragging,
  isDropTarget
}: {
  pose: Pose;
  index: number;
  onDelete: (index: number) => void;
  onDragStart: (e: React.DragEvent, index: number) => void;
  onDragOver: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent, dropIndex: number) => void;
  onDragEnd: () => void;
  isDragging: boolean;
  isDropTarget: boolean;
}) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div
      className={cn(
        "border-b last:border-b-0 border-gray-200 dark:border-gray-800 transition-all duration-200",
        isDragging && "opacity-50 scale-95",
        isDropTarget && "bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700"
      )}
      draggable
      onDragStart={(e) => onDragStart(e, index)}
      onDragOver={onDragOver}
      onDrop={(e) => onDrop(e, index)}
      onDragEnter={(e) => e.preventDefault()}
      onDragEnd={onDragEnd}
    >
      <div className="p-3 flex items-start group">
        {/* Drag Handle */}
        <div className="flex items-center mr-2">
          <GripVertical className="h-4 w-4 text-muted-foreground cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>

        {/* Main Content */}
        <div
          className="flex-1 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors rounded px-2 py-1 -mx-2 -my-1"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex items-center gap-2 mb-1">
            <MessageSquareQuote className="h-4 w-4 text-primary" />
            <span className="font-medium text-sm">{pose.character_name}</span>
            {pose.timestamp && (
              <span className="text-xs text-muted-foreground ml-auto">
                {new Date(pose.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>

          <div className={cn(
            "text-sm whitespace-pre-wrap",
            isExpanded ? "" : "line-clamp-1 text-muted-foreground"
          )}>
            {isExpanded ? pose.content : (pose.preview || pose.content.slice(0, 80) + (pose.content.length > 80 ? '...' : ''))}
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-1 ml-2 pt-1">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(index);
            }}
            className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-500 hover:text-red-700 dark:hover:text-red-400"
            title="Delete pose"
          >
            <X className="h-3 w-3" />
          </button>

          <div className="text-muted-foreground">
            {isExpanded ?
              <ChevronUp className="h-4 w-4" /> :
              <ChevronDown className="h-4 w-4" />}
          </div>
        </div>
      </div>
    </div>
  )
}

// Character type definition
interface Character {
  id: string;
  name: string;
  background?: string;
  personality?: string;
  skills?: string;
  goals?: string;
  relationships?: string;
  voice_notes?: string;
}

interface PostEditorProps {
  onContextUpdate?: (context: PoseContext | null, suggestions: ResponseSuggestion[], loading: boolean, error: string | null) => void;
  autoLoadSceneId?: string | null;
  onSeedPostText?: (seedFunction: (text: string) => void) => void;
}

export function PostEditor({ onContextUpdate, autoLoadSceneId, onSeedPostText }: PostEditorProps) {
  const [sceneText, setSceneText] = useState(initialScene)
  const [postText, setPostText] = useState(initialPost)
  const [enhancedPost, setEnhancedPost] = useState("")
  const [enhancementStyle, setEnhancementStyle] = useState("balanced")
  const [includeEnvironmentalDetails, setIncludeEnvironmentalDetails] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const [isSaving, setIsSaving] = useState(false)
  const [sceneContext, setSceneContext] = useState<PoseContext | null>(null)
  const [responseSuggestions, setResponseSuggestions] = useState<ResponseSuggestion[]>([])
  const [contextError, setContextError] = useState<string | null>(null)
  const [characters, setCharacters] = useState<Character[]>([])
  const [currentCharacter, setCurrentCharacter] = useState<string>("")
  const [isLoadingCharacters, setIsLoadingCharacters] = useState(true)
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [sceneTitle, setSceneTitle] = useState("") // New state for scene title
  const [sceneId, setSceneId] = useState<string | null>(null) // Track if scene is saved
  const debouncedSceneText = useDebounce(sceneText, 500)
  const { toast } = useToast()

  // Drag and drop state
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null)
  const [showAllPoses, setShowAllPoses] = useState(false)

  const { getToken } = useAuth() // Ensure useAuth is imported at top (it is NOT imported in original file based on view)
  // Copy/newline settings state
  const [newlineReplacement, setNewlineReplacement] = useState("\\n")
  const [showCopySettings, setShowCopySettings] = useState(false)

  // Drag and drop handlers
  const handleDragStart = (e: React.DragEvent, index: number) => {
    setDraggedIndex(index)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/html', '')
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDragEnter = (e: React.DragEvent, index: number) => {
    e.preventDefault()
    setDragOverIndex(index)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOverIndex(null)
  }

  const handleDrop = (e: React.DragEvent, dropIndex: number) => {
    e.preventDefault()

    if (draggedIndex === null || draggedIndex === dropIndex) {
      setDraggedIndex(null)
      setDragOverIndex(null)
      return
    }

    if (!sceneContext?.poses) return

    const newPoses = [...sceneContext.poses]
    const draggedPose = newPoses[draggedIndex]

    // Remove the dragged item
    newPoses.splice(draggedIndex, 1)

    // Insert at new position
    const insertIndex = draggedIndex < dropIndex ? dropIndex - 1 : dropIndex
    newPoses.splice(insertIndex, 0, draggedPose)

    // Update the scene context
    const updatedContext = {
      ...sceneContext,
      poses: newPoses
    }

    setSceneContext(updatedContext)

    // Update parent component
    if (onContextUpdate) {
      onContextUpdate(updatedContext, responseSuggestions, false, null)
    }

    setDraggedIndex(null)
    setDragOverIndex(null)
  }

  const handleDragEnd = () => {
    setDraggedIndex(null)
    setDragOverIndex(null)
  }

  // Delete pose handler
  const handleDeletePose = (index: number) => {
    if (!sceneContext?.poses) return

    const newPoses = [...sceneContext.poses]
    newPoses.splice(index, 1)

    const updatedContext = {
      ...sceneContext,
      poses: newPoses
    }

    setSceneContext(updatedContext)

    // Update parent component
    if (onContextUpdate) {
      onContextUpdate(updatedContext, responseSuggestions, false, null)
    }

    toast({
      title: "Pose deleted",
      description: "The pose has been removed from the scene.",
    })
  }

  // Effect to set current character once characters are loaded
  useEffect(() => {
    if (characters.length > 0 && currentCharacter === "") {
      setCurrentCharacter(characters[0].id)
    }
  }, [characters, currentCharacter])

  // Effect to expose post text seeding to parent component
  useEffect(() => {
    if (onSeedPostText) {
      onSeedPostText(setPostText)
    }
  }, [onSeedPostText])

  // Effect to automatically load scene if autoLoadSceneId is provided
  useEffect(() => {
    if (autoLoadSceneId && characters.length > 0 && sceneId !== autoLoadSceneId) {
      const loadScene = async () => {
        try {
          const token = await getToken();
          const headers: Record<string, string> = {
            'Content-Type': 'application/json',
          };

          if (token) {
            headers['Authorization'] = `Bearer ${token}`;
          }

          const sceneUrl = `${getApiUrl()}/api/scenes/${autoLoadSceneId}`;
          const response = await fetch(sceneUrl, { headers });

          if (response.ok) {
            const data = await response.json();
            if (data.success && data.data) {
              const { context, character_id, name } = data.data;
              // Call the handleSceneSelected function with the loaded data
              await handleSceneSelected(autoLoadSceneId, name, context || {}, character_id || "");
            }
          }
        } catch (error) {
          console.error('Error auto-loading scene:', error);
          toast({
            title: "Error",
            description: "Failed to load scene automatically",
            variant: "destructive",
          });
        }
      };

      loadScene();
    }
  }, [autoLoadSceneId, characters, sceneId])

  // Effect to listen for scene poses updates
  useEffect(() => {
    // Handler for the custom event
    const handleScenePosesUpdated = async (event: Event) => {
      const customEvent = event as CustomEvent;
      const updatedSceneId = customEvent.detail?.sceneId;

      // Only refresh if this is the current scene
      if (updatedSceneId && updatedSceneId === sceneId) {
        try {
          console.log('Scene poses updated, refreshing poses view...');

          const token = await getToken();
          const headers: Record<string, string> = {
            'Content-Type': 'application/json',
          };

          if (token) {
            headers['Authorization'] = `Bearer ${token}`;
          }

          // Fetch the updated poses for this scene
          const posesUrl = `${getApiUrl()}/api/scenes/${sceneId}/poses`;
          const posesResponse = await fetch(posesUrl, { headers });

          if (posesResponse.ok) {
            const posesData = await posesResponse.json();

            if (posesData.success && posesData.data && Array.isArray(posesData.data)) {
              // Create enhanced context with updated poses
              const updatedPoses = posesData.data.map((pose: any) => ({
                character_name: pose.character_name,
                content: pose.pose_text,
                timestamp: pose.created_at,
                preview: pose.pose_text.slice(0, 80) + (pose.pose_text.length > 80 ? '...' : '')
              }));

              // Update the scene context with the new poses
              const updatedContext = {
                // Ensure all required array properties have default empty arrays
                actions: sceneContext?.actions || [],
                character_interactions: sceneContext?.character_interactions || [],
                emotions: sceneContext?.emotions || [],
                environmental_details: sceneContext?.environmental_details || [],
                responseHooks: sceneContext?.responseHooks || [],
                // Include all other properties from the existing context
                ...(sceneContext || {}),
                // Override with the new poses
                poses: updatedPoses
              };

              // Update the state
              setSceneContext(updatedContext);

              // Update parent component
              if (onContextUpdate) {
                onContextUpdate(updatedContext, responseSuggestions, false, null);
              }

              toast({
                title: "Scene Poses Updated",
                description: `Refreshed ${updatedPoses.length} poses in the scene.`
              });
            }
          }
        } catch (error) {
          console.error('Error refreshing scene poses:', error);
        }
      }
    };

    // Add event listener for the custom event
    window.addEventListener('scene-poses-updated', handleScenePosesUpdated);

    // Also listen for storage events (for cross-tab updates)
    const handleStorageEvent = (event: StorageEvent) => {
      if (event.key === 'scene-poses-updated') {
        try {
          const data = JSON.parse(event.newValue || '{}');
          if (data.sceneId === sceneId) {
            // Create a synthetic custom event
            const syntheticEvent = new CustomEvent('scene-poses-updated', {
              detail: data
            });
            handleScenePosesUpdated(syntheticEvent);
          }
        } catch (error) {
          console.error('Error handling storage event:', error);
        }
      }
    };

    window.addEventListener('storage', handleStorageEvent);

    // Clean up event listeners
    return () => {
      window.removeEventListener('scene-poses-updated', handleScenePosesUpdated);
      window.removeEventListener('storage', handleStorageEvent);
    };
  }, [sceneId, sceneContext, onContextUpdate, responseSuggestions, toast])

  // Load characters from the backend when component mounts
  useEffect(() => {
    const fetchCharacters = async () => {
      setIsLoadingCharacters(true);
      try {
        // Get the access token
        const accessToken = await getToken();

        if (!accessToken) {
          console.warn('No access token found');
          // Don't throw if just not logged in, maybe check isAuthenticated? 
          // But existing code throws. I'll stick to throwing or handling.
          // If no token, maybe return?
          // Existing code: throws 'Authentication required'.
          // I'll keep behavior.
          throw new Error('Authentication required');
        }

        const response = await fetch(`${getApiUrl()}/api/characters/`, {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`
          }
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch characters: ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.data) {
          // Log to verify character structure
          console.log('Fetched characters:', data.data);

          // Ensure all characters have valid IDs
          const validatedCharacters = data.data.map((char: any) => {
            // Use name as fallback ID if ID is missing
            if (!char.id) {
              console.log('Character missing ID:', char);
              return { ...char, id: char.name || `character-${Math.random().toString(36).substr(2, 9)}` };
            }
            return char;
          });

          setCharacters(validatedCharacters);
          // Set the current character to the first one if available
          if (validatedCharacters.length > 0) {
            setCurrentCharacter(validatedCharacters[0].id);
          }
        } else {
          console.warn('Characters API returned success: false or no data');
        }
      } catch (error) {
        console.error('Error fetching characters:', error);
        toast({
          title: "Couldn't load characters",
          description: "Using default character list instead.",
          variant: "destructive"
        });
      } finally {
        setIsLoadingCharacters(false);
      }
    };

    fetchCharacters();
  }, [toast]);



  // Handle post enhancement with backend API
  const handleEnhance = async () => {
    // Create empty context if none exists
    const contextToUse = sceneContext || {
      poses: [],
      actions: [],
      character_interactions: [],
      emotions: ["neutral"],
      environmental_details: [],
      responseHooks: [],
      scene_timing: "Present",
      urgency_level: "medium",
      narrative_tone: "neutral"
    };

    // Check if characters exist
    if (characters.length === 0) {
      toast({
        title: "No characters available",
        description: "Please create at least one character before enhancing posts.",
        variant: "destructive"
      })
      return
    }

    if (!postText.trim()) {
      toast({
        title: "Missing post content",
        description: "Please enter text for your post before enhancing.",
        variant: "destructive"
      })
      return
    }

    setIsLoading(true)
    setEnhancedPost("")

    try {
      const selectedCharacter = characters.find(c => c.id === currentCharacter)
      const characterData = selectedCharacter ? {
        name: selectedCharacter.name,
        background: selectedCharacter.background || "",
        personality: selectedCharacter.personality || "",
        skills: selectedCharacter.skills || "",
        goals: selectedCharacter.goals || "",
        relationships: selectedCharacter.relationships || "",
        voice_notes: selectedCharacter.voice_notes || ""
      } : undefined

      // Convert poses to context text for the API (if any poses exist)
      const contextText = contextToUse.poses && contextToUse.poses.length > 0
        ? contextToUse.poses.map(pose => `${pose.character_name}: ${pose.content}`).join('\n\n')
        : "No previous context available.";

      // Create enhanced context object with poses converted to text
      const enhancedContext = {
        ...contextToUse,
        contextText, // Add the formatted poses as context text
        poses: contextToUse.poses || [] // Keep the original poses array or empty array
      }

      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      const result = await enhancePose(postText, enhancedContext, characterData, enhancementStyle, token, includeEnvironmentalDetails)

      if (result.success) {
        setEnhancedPost(result.enhanced_pose)
      } else {
        toast({
          title: "Enhancement failed",
          description: result.error || "Failed to enhance post",
          variant: "destructive"
        })
      }
    } catch (error) {
      toast({
        title: "Enhancement error",
        description: error instanceof Error ? error.message : "An unknown error occurred",
        variant: "destructive"
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleCopy = () => {
    // Apply newline replacement if specified
    let textToCopy = enhancedPost
    if (newlineReplacement && newlineReplacement !== "\\n") {
      // Replace actual newlines with the custom replacement
      textToCopy = enhancedPost.replace(/\n/g, newlineReplacement)
    }

    navigator.clipboard.writeText(textToCopy)
    toast({
      title: "Copied to clipboard!",
      description: newlineReplacement !== "\\n" ?
        `Text copied with "${newlineReplacement}" as newlines.` :
        "The enhanced post is ready to be pasted.",
    })
  }

  const handleAddToContext = () => {
    if (!enhancedPost) return

    const selectedCharacter = characters.find(c => c.id === currentCharacter)
    const characterName = selectedCharacter?.name || "Unknown Character"

    // Create a new pose object from the enhanced post
    const newPose: Pose = {
      character_name: characterName,
      content: enhancedPost,
      timestamp: new Date().toISOString(),
      preview: enhancedPost.slice(0, 80) + (enhancedPost.length > 80 ? '...' : '')
    }

    // Create base context if none exists
    const baseContext: PoseContext = sceneContext || {
      poses: [],
      actions: [],
      character_interactions: [],
      emotions: ["neutral"],
      environmental_details: [],
      responseHooks: [],
      scene_timing: "Present",
      urgency_level: "medium",
      narrative_tone: "neutral"
    };

    // Add to the scene context
    const updatedPoses = [...(baseContext.poses || []), newPose]
    const updatedContext = {
      ...baseContext,
      poses: updatedPoses,
      character_interactions: Array.from(new Set([...baseContext.character_interactions, characterName])).slice(0, 5)
    }

    setSceneContext(updatedContext)

    // Update parent component
    if (onContextUpdate) {
      onContextUpdate(updatedContext, responseSuggestions, false, null)
    }

    toast({
      title: "Added to context!",
      description: `Enhanced post added as ${characterName}'s pose.`,
    })
  }

  // Save the current scene
  const handleSaveScene = async () => {
    if (!sceneTitle.trim()) {
      toast({
        title: "Title Required",
        description: "Please enter a title for your scene before saving.",
        variant: "destructive",
      });
      return;
    }

    // Create a default context if none exists
    const contextToSave = sceneContext || {
      poses: [],
      actions: [],
      character_interactions: [],
      emotions: ["neutral"],
      environmental_details: [],
      responseHooks: [],
      scene_timing: "Present",
      urgency_level: "medium",
      narrative_tone: "neutral"
    };

    setIsSaving(true);
    try {
      const accessToken = await getToken();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      };

      if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
      }

      // Create payload with title and context data including poses
      const payload = {
        name: sceneTitle,
        character_id: currentCharacter,
        // Save the context object including poses
        context: {
          actions: contextToSave.actions || [],
          character_interactions: contextToSave.character_interactions || [],
          emotions: contextToSave.emotions || ["neutral"],
          environmental_details: contextToSave.environmental_details || [],
          responseHooks: contextToSave.responseHooks || [],
          scene_timing: contextToSave.scene_timing || "Present",
          urgency_level: contextToSave.urgency_level || contextToSave.urgency || "medium",
          narrative_tone: contextToSave.narrative_tone || contextToSave.tone || "neutral",
          poses: contextToSave.poses || [] // Include poses in the saved context
        },
      };

      // If we have a scene ID, update it; otherwise create new
      const baseUrl = getApiUrl();
      const url = sceneId
        ? `${baseUrl}/api/scenes/${sceneId}`
        : `${baseUrl}/api/scenes`;

      const method = sceneId ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers,
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to save scene');
      }

      const data = await response.json();

      // If this was a new scene, store the ID
      if (!sceneId && data.data?._id) {
        setSceneId(data.data._id);
      }

      toast({
        title: "Scene Saved",
        description: "Your scene has been saved successfully.",
      });

      // Trigger refresh of recent scenes
      localStorage.setItem('sceneUpdated', 'true');
      // Trigger storage event for same-tab updates
      window.dispatchEvent(new StorageEvent('storage', {
        key: 'sceneUpdated',
        newValue: 'true',
        storageArea: localStorage
      }));

    } catch (error) {
      console.error('Error saving scene:', error);
      toast({
        title: "Error Saving Scene",
        description: error instanceof Error ? error.message : 'An unknown error occurred',
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  // Handler for scene dump processing completion
  const handleSceneDumpProcessingComplete = async (result: SceneDumpProcessingResult) => {
    if (result.success) {
      // Convert processed poses to context format
      const newPoses: Pose[] = result.poses.map(pose => ({
        character_name: pose.character_name,
        content: pose.pose_text,
        timestamp: pose.timestamp,
        preview: pose.pose_text.substring(0, 80) + (pose.pose_text.length > 80 ? '...' : '')
      }))

      // Get existing poses or empty array if none exist
      const existingPoses = sceneContext?.poses || [];

      // Combine existing and new poses
      const combinedPoses = [...existingPoses, ...newPoses];

      // Create base context if none exists
      const baseContext: PoseContext = sceneContext || {
        poses: [],
        actions: [],
        character_interactions: [],
        emotions: ["neutral"],
        environmental_details: [],
        responseHooks: [],
        scene_timing: "Present",
        urgency_level: "medium",
        narrative_tone: "neutral"
      };

      // Create updated scene context with combined poses
      const updatedContext: PoseContext = {
        ...baseContext,
        poses: combinedPoses,
        actions: combinedPoses.map(p => p.content).slice(-3), // Take the 3 most recent actions
        character_interactions: Array.from(new Set(combinedPoses.map(p => p.character_name))).slice(0, 5),
        emotions: ["engaged", "focused"],
        environmental_details: baseContext.environmental_details,
        responseHooks: ["Continue the scene", "Respond to recent actions"],
        scene_timing: "Present",
        urgency_level: "medium",
        narrative_tone: "immersive"
      }

      setSceneContext(updatedContext)

      // Update parent component
      if (onContextUpdate) {
        onContextUpdate(updatedContext, [], false, null)
      }

      // Clear the scene text since poses have been processed
      setSceneText('')

      // Trigger a refresh of the scene-weaver poses view
      if (typeof window !== 'undefined' && sceneId) {
        // Create and dispatch a custom event to notify scene-weaver to refresh
        const refreshEvent = new CustomEvent('scene-poses-updated', {
          detail: {
            sceneId,
            posesCount: result.importedCount,
            timestamp: new Date().toISOString()
          }
        });
        window.dispatchEvent(refreshEvent);
      }

      toast({
        title: "Scene Processed Successfully",
        description: `Added ${result.importedCount} poses to your scene context.`
      })


    }
  }

  // Handler for when a scene is selected from the SceneSelector
  const handleSceneSelected = async (sceneId: string, title: string, context: PoseContext, characterId: string) => {
    // Update the editor state with the loaded scene data
    setSceneId(sceneId);
    setSceneTitle(title);

    // If the character exists in our characters list, set it as current
    if (characterId && characters.some(char => char.id === characterId)) {
      setCurrentCharacter(characterId);
    }

    // Fetch poses for this scene
    try {
      const token = localStorage.getItem('access_token');
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const posesUrl = `${getApiUrl()}/api/scenes/${sceneId}/poses`;
      const posesResponse = await fetch(posesUrl, { headers });

      if (posesResponse.ok) {
        const posesData = await posesResponse.json();

        if (posesData.success && posesData.data && Array.isArray(posesData.data) && posesData.data.length > 0) {
          // Create enhanced context with poses from API
          const enhancedContext = {
            ...context,
            poses: posesData.data.map((pose: any) => ({
              character_name: pose.character_name,
              content: pose.pose_text,
              timestamp: pose.created_at,
              preview: pose.pose_text.slice(0, 80) + (pose.pose_text.length > 80 ? '...' : '')
            }))
          };

          // Set the context with poses
          setSceneContext(enhancedContext);
          if (onContextUpdate) {
            onContextUpdate(enhancedContext, [], false, null);
          }

          toast({
            title: "Scene Loaded",
            description: `"${title}" loaded with ${posesData.data.length} poses.`
          });
        } else {
          // No poses in API response, check if poses are in the saved context
          const existingPoses = context.poses || [];

          if (existingPoses.length > 0) {
            // We have poses in the saved context, use them
            setSceneContext(context);
            if (onContextUpdate) {
              onContextUpdate(context, [], false, null);
            }

            toast({
              title: "Scene Loaded",
              description: `"${title}" loaded with ${existingPoses.length} poses from saved context.`
            });
          } else {
            // No poses anywhere, just use the saved context
            setSceneContext(context);
            if (onContextUpdate) {
              onContextUpdate(context, [], false, null);
            }

            toast({
              title: "Scene Loaded",
              description: `"${title}" loaded (no poses found).`
            });
          }
        }
      } else {
        console.error('Failed to fetch poses:', posesResponse.status);
        // Fall back to saved context
        setSceneContext(context);
        if (onContextUpdate) {
          onContextUpdate(context, [], false, null);
        }

        toast({
          title: "Scene Loaded",
          description: `"${title}" loaded. Could not fetch poses.`
        });
      }
    } catch (error) {
      console.error('Error loading scene poses:', error);
      // Fall back to saved context
      setSceneContext(context);
      if (onContextUpdate) {
        onContextUpdate(context, [], false, null);
      }

      toast({
        title: "Scene Loaded",
        description: `"${title}" loaded. Error fetching poses.`
      });
    }
  };

  return (
    <div className="grid gap-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Scene Context</CardTitle>
            <CardDescription>The ongoing narrative and previous posts.</CardDescription>
          </div>
          <SceneSelector onSceneSelected={handleSceneSelected} />
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="scene-title">Scene Title</Label>
            <Input
              id="scene-title"
              placeholder="Enter a title for your scene..."
              value={sceneTitle}
              onChange={(e) => setSceneTitle(e.target.value)}
            />
          </div>

          {/* Display poses when available from context */}
          {sceneContext?.poses && sceneContext.poses.length > 0 && (
            <div className="mt-4 pt-2 border-t">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold flex items-center gap-2 text-muted-foreground">
                  <MessageSquareQuote className="h-4 w-4" />
                  Scene Poses ({sceneContext.poses.length})
                </h3>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAllPoses(!showAllPoses)}
                    className="text-xs"
                  >
                    {showAllPoses ? 'Show Recent' : 'View All'}
                  </Button>
                </div>
              </div>


              <div className="rounded-md bg-gray-50 dark:bg-gray-900">
                {sceneContext.poses && (showAllPoses ? sceneContext.poses : sceneContext.poses.slice(Math.max(0, sceneContext.poses.length - 5)))
                  .map((pose, index) => {
                    const actualIndex = showAllPoses ? index : Math.max(0, sceneContext.poses!.length - 5) + index
                    return (
                      <CollapsiblePose
                        key={`pose-${actualIndex}`}
                        pose={pose}
                        index={actualIndex}
                        onDelete={handleDeletePose}
                        onDragStart={handleDragStart}
                        onDragOver={handleDragOver}
                        onDrop={handleDrop}
                        onDragEnd={handleDragEnd}
                        isDragging={draggedIndex === actualIndex}
                        isDropTarget={dragOverIndex === actualIndex}
                      />
                    )
                  })}
              </div>
            </div>
          )}
        </CardContent>
        <CardFooter className="justify-end space-x-2">
          <Button
            onClick={handleSaveScene}
            variant="outline"
            disabled={isSaving || !sceneTitle.trim()}
          >
            {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
            {sceneId ? 'Update Scene' : 'Save Scene'}
          </Button>
        </CardFooter>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Scene Dump</CardTitle>
          <CardDescription>
            Paste raw scene text here. The Scene Dump Processor below will automatically extract and organize poses with advanced analysis.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Textarea
            id="scene-input"
            value={sceneText}
            onChange={(e) => setSceneText(e.target.value)}
            className="min-h-24 font-mono text-sm resize-y"
            placeholder="> Paste your entire scene here. Don't worry about length - this field can hold a lot of text..."
            maxLength={100000}
          />
        </CardContent>
      </Card>

      {/* Scene Dump Processor */}
      <SceneDumpProcessor
        sceneDumpText={sceneText}
        sceneId={sceneId ?? undefined}
        sceneTitle={sceneTitle}
        onProcessingComplete={handleSceneDumpProcessingComplete}
        autoProcess={false}
        className="mb-6"
      />

      <Card>
        <CardHeader>
          <CardTitle>Your Post & Controls</CardTitle>
          <CardDescription>Enter your specific post and choose the enhancement style. The AI will use any available poses as context.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="post-input">Your Post</Label>
            <Textarea
              id="post-input"
              value={postText}
              onChange={(e) => setPostText(e.target.value)}
              className="min-h-20 font-mono text-sm"
              placeholder="Jax looks around the room."
            />
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label htmlFor="character-select">Character Profile</Label>
              {isLoadingCharacters ? (
                <div className="flex h-10 w-full items-center rounded-md border border-input bg-background px-3 py-2">
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  <span className="text-sm">Loading characters...</span>
                </div>
              ) : (
                <div className="relative">
                  {/* Implement a simplified dropdown using standard components to avoid Radix UI key issues */}
                  <button
                    id="character-select"
                    type="button"
                    className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 [&>span]:line-clamp-1"
                    onClick={() => setDropdownOpen(!dropdownOpen)}
                    aria-haspopup="listbox"
                    aria-expanded={dropdownOpen}
                  >
                    {currentCharacter && characters.find(c => c.id === currentCharacter)?.name ? (
                      characters.find(c => c.id === currentCharacter)?.name
                    ) : (
                      <span className="text-muted-foreground">Select a character profile...</span>
                    )}
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4 opacity-50"><path d="m6 9 6 6 6-6" /></svg>
                  </button>

                  {dropdownOpen && (
                    <div className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-md border bg-popover text-popover-foreground shadow-md" role="listbox">
                      <div className="p-1">
                        {characters.length > 0 ? characters.map((char) => {
                          const isSelected = currentCharacter === char.id;
                          return (
                            <div
                              key={char.id}
                              className={`relative flex w-full cursor-pointer select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none ${isSelected ? 'bg-accent text-accent-foreground' : ''} hover:bg-accent hover:text-accent-foreground`}
                              onClick={() => {
                                console.log('Character selected:', char.id, char.name);
                                setCurrentCharacter(char.id);
                                setDropdownOpen(false);
                              }}
                              role="option"
                              aria-selected={isSelected}
                              data-state={isSelected ? 'checked' : 'unchecked'}
                              tabIndex={0}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ') {
                                  setCurrentCharacter(char.id);
                                  setDropdownOpen(false);
                                }
                              }}
                            >
                              {isSelected && (
                                <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
                                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><polyline points="20 6 9 17 4 12" /></svg>
                                </span>
                              )}
                              <span className="font-medium">{char.name}</span>
                            </div>
                          );
                        }) : (
                          <div className="py-2 px-1 text-sm text-center text-amber-800">
                            <div className="flex items-center justify-center gap-1 mb-2">
                              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                              No characters available
                            </div>
                            <div className="text-xs">Please create a character first</div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
            <div className="space-y-2">
              <Label>Enhancement Style</Label>
              <Tabs value={enhancementStyle} onValueChange={setEnhancementStyle}>
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="minimal" key="minimal">Minimal</TabsTrigger>
                  <TabsTrigger value="balanced" key="balanced">Balanced</TabsTrigger>
                  <TabsTrigger value="elaborate" key="elaborate">Elaborate</TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="environmental-details"
                className="h-4 w-4 rounded border-gray-300 focus:ring-primary"
                checked={includeEnvironmentalDetails}
                onChange={(e) => setIncludeEnvironmentalDetails(e.target.checked)}
              />
              <Label htmlFor="environmental-details" className="text-sm font-normal">Include environmental details</Label>
            </div>
          </div>
        </CardContent>
        <CardFooter className="justify-end">
          <Button onClick={handleEnhance} disabled={isLoading || !postText.trim()}>
            {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Wand2 className="mr-2 h-4 w-4" />}
            Enhance Post
          </Button>
        </CardFooter>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Enhanced Narrative</CardTitle>
            <CardDescription>Your AI-crafted result. Ready to copy and paste.</CardDescription>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => setShowCopySettings(!showCopySettings)}
              disabled={isLoading || !enhancedPost}
            >
              <Settings className="h-3.5 w-3.5" />
              <span className="sr-only">Copy Settings</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={handleAddToContext}
              disabled={isLoading || !enhancedPost}
            >
              <Plus className="h-3.5 w-3.5" />
              <span className="sr-only">Add to Context</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={handleCopy}
              disabled={isLoading || !enhancedPost}
            >
              <Copy className="h-3.5 w-3.5" />
              <span className="sr-only">Copy</span>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {showCopySettings && (
            <div className="mb-4 p-4 rounded-lg border bg-muted/30 space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="newline-replacement" className="text-sm font-medium">
                  Newline Replacement
                </Label>
                <p className="text-xs text-muted-foreground">
                  Customize how newlines are copied
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Input
                  id="newline-replacement"
                  value={newlineReplacement}
                  onChange={(e) => setNewlineReplacement(e.target.value)}
                  placeholder="\\n"
                  className="max-w-24 font-mono text-sm"
                />
                <div className="flex gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setNewlineReplacement("\\n")}
                    className="text-xs"
                  >
                    \\n
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setNewlineReplacement("%r")}
                    className="text-xs"
                  >
                    %r
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setNewlineReplacement("%R")}
                    className="text-xs"
                  >
                    %R
                  </Button>
                </div>
              </div>
            </div>
          )}
          <div className="relative rounded-lg bg-muted/50 p-4 min-h-48">
            {isLoading ? (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : (
              <pre className="font-serif text-base leading-relaxed whitespace-pre-wrap bg-transparent border-0 p-0 overflow-visible">
                {enhancedPost}
              </pre>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
