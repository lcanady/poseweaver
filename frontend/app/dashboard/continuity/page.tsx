"use client"

import { useState, useEffect } from "react"
import { ContinuityDashboard } from "@/components/continuity/continuity-dashboard"
import { CharacterConsistencyScoreDisplay } from "@/components/continuity/character-consistency-score-display"
import { PlotThreadTrackingInterface } from "@/components/continuity/plot-thread-tracking-interface"
import { RelationshipDynamicsVisualization } from "@/components/continuity/relationship-dynamics-visualization"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Shield, AlertTriangle, Users, Plus, Target, GitBranch, Activity } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import Link from "next/link"
import type { Scene } from "@/types/scene"

interface ContinuityPageState {
  scenes: Scene[]
  selectedSceneId: string | null
  loading: boolean
  error: string | null
  activeTab: string
}

export default function ContinuityPage() {
  const [state, setState] = useState<ContinuityPageState>({
    scenes: [],
    selectedSceneId: null,
    loading: true,
    error: null,
    activeTab: "overview"
  })
  const { toast } = useToast()

  useEffect(() => {
    fetchScenes()
  }, [])

  const fetchScenes = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }))
      
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/scenes`, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success && data.data) {
          const scenes = data.data
          setState(prev => ({
            ...prev,
            scenes: scenes,
            selectedSceneId: scenes.length > 0 ? ((scenes[0] as any)._id || scenes[0].id) : null,
            loading: false
          }))
        } else {
          setState(prev => ({ ...prev, error: 'Failed to load scenes', loading: false }))
        }
      } else {
        setState(prev => ({ ...prev, error: 'Failed to load scenes', loading: false }))
      }
    } catch (error) {
      console.error('Error fetching scenes:', error)
      setState(prev => ({ ...prev, error: 'Failed to load scenes', loading: false }))
    }
  }

  const handleSceneSelect = (sceneId: string) => {
    setState(prev => ({ ...prev, selectedSceneId: sceneId }))
  }

  const handleTabChange = (tab: string) => {
    setState(prev => ({ ...prev, activeTab: tab }))
  }

  const handleFlagResolve = async (flagId: string, resolution: string) => {
    toast({
      title: "Flag Resolved",
      description: "The continuity flag has been resolved successfully.",
      variant: "default",
    })
  }

  const handleCharacterStateUpdate = async (characterId: string, updates: any) => {
    toast({
      title: "Character Updated",
      description: "Character state has been updated successfully.",
      variant: "default",
    })
  }

  const handleEnvironmentStateUpdate = async (environmentId: string, updates: any) => {
    toast({
      title: "Environment Updated",
      description: "Environment state has been updated successfully.",
      variant: "default",
    })
  }

  const handleAnalyzeContent = async (content: string, analysisType: string) => {
    toast({
      title: "Analysis Started",
      description: "Content analysis has been initiated.",
      variant: "default",
    })
  }

  // Mock data for the new components - replace with real API calls
  const mockConsistencyData = {
    character_id: 'char-1',
    character_name: 'Main Character',
    consistency_score: 87,
    recent_inconsistencies: [
      {
        id: 'inc-1',
        timestamp: new Date().toISOString(),
        description: 'Character displayed different personality traits than established',
        severity: 'medium' as const,
        pose_id: 'pose-123',
        resolved: false
      }
    ]
  }

  const mockPlotThreads = [
    {
      thread_id: 'thread-1',
      thread_name: 'The Ancient Mystery',
      thread_description: 'Investigation into ancient artifacts',
      thread_status: 'active' as const,
      importance: 'major' as const,
      created_timestamp: new Date().toISOString(),
      last_updated_timestamp: new Date().toISOString(),
      related_characters: [
        {
          character_id: 'char-1',
          character_name: 'Main Character',
          relevance: 'primary' as const
        }
      ],
      thread_elements: [
        {
          element_id: 'elem-1',
          thread_id: 'thread-1',
          element_type: 'clue' as const,
          element_name: 'Strange Symbol',
          element_description: 'Mysterious symbol found on artifact',
          timestamp: new Date().toISOString(),
          status: 'introduced' as const,
          related_characters: []
        }
      ],
      scenes: [
        {
          scene_id: state.selectedSceneId || '',
          scene_name: 'Current Scene',
          last_activity: new Date().toISOString()
        }
      ]
    }
  ]

  const mockRelationships = [
    {
      relationship_id: 'rel-1',
      character_id: 'char-1',
      character_name: 'Main Character',
      related_character_id: 'char-2',
      related_character_name: 'Supporting Character',
      relationship_type: 'friend',
      dynamics: [
        {
          timestamp: new Date(Date.now() - 86400000).toISOString(),
          trust_level: 7,
          tension_level: 2,
          description: 'Positive interaction during investigation'
        },
        {
          timestamp: new Date().toISOString(),
          trust_level: 8,
          tension_level: 1,
          description: 'Trust strengthened through shared danger'
        }
      ]
    }
  ]

  const selectedScene = state.scenes.find(scene => ((scene as any)._id || scene.id) === state.selectedSceneId)

  if (state.loading) {
    return (
      <div className="flex-1 p-4 md:p-8">
        <div className="mx-auto w-full max-w-7xl">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <Shield className="h-12 w-12 animate-pulse text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">Loading continuity dashboard...</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (state.error) {
    return (
      <div className="flex-1 p-4 md:p-8">
        <div className="mx-auto w-full max-w-7xl">
          <Card>
            <CardContent className="p-8 text-center">
              <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Error Loading Dashboard</h3>
              <p className="text-muted-foreground mb-4">{state.error}</p>
              <Button onClick={fetchScenes}>Try Again</Button>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  if (state.scenes.length === 0) {
    return (
      <div className="flex-1 p-4 md:p-8">
        <div className="mx-auto w-full max-w-7xl">
          <div className="mb-8">
            <h1 className="text-3xl font-bold tracking-tight">Continuity Dashboard</h1>
            <p className="text-muted-foreground mt-1">
              Track and manage story continuity across your scenes
            </p>
          </div>
          
          <Card>
            <CardContent className="p-8 text-center">
              <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Scenes Found</h3>
              <p className="text-muted-foreground mb-4">
                You need to create scenes first to use the continuity dashboard. 
                Scenes allow you to track characters, environments, and plot elements.
              </p>
              <div className="flex items-center justify-center gap-2">
                <Button asChild>
                  <Link href="/dashboard/scenes">
                    <Plus className="h-4 w-4 mr-2" />
                    Create Scene
                  </Link>
                </Button>
                <Button variant="outline" asChild>
                  <Link href="/dashboard/scene-weaver">
                    Start Scene Weaver
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="mx-auto w-full max-w-7xl space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Continuity Dashboard</h1>
            <p className="text-muted-foreground mt-1">
              Track and manage story continuity across your scenes
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-sm">
              {state.scenes.length} Scene{state.scenes.length !== 1 ? 's' : ''}
            </Badge>
          </div>
        </div>

        {/* Scene Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Select Scene
            </CardTitle>
            <CardDescription>
              Choose a scene to view its continuity information
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <Select value={state.selectedSceneId || ""} onValueChange={handleSceneSelect}>
                <SelectTrigger className="w-64">
                  <SelectValue placeholder="Choose a scene..." />
                </SelectTrigger>
                <SelectContent>
                  {state.scenes.map((scene, index) => {
                    const sceneId = (scene as any)._id || scene.id || `scene-${index}`
                    return (
                      <SelectItem key={sceneId} value={sceneId}>
                        <div className="flex items-center justify-between w-full">
                          <span>{scene.name}</span>
                          <Badge variant="outline" className="ml-2">
                            {scene.status || 'active'}
                          </Badge>
                        </div>
                      </SelectItem>
                    )
                  })}
                </SelectContent>
              </Select>
              
              {selectedScene && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>Characters: {(selectedScene as any).participants?.length || 0}</span>
                  <span>•</span>
                  <span>Poses: {(selectedScene as any).poses?.length || 0}</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Main Continuity Features */}
        {selectedScene && (
          <Tabs value={state.activeTab} onValueChange={handleTabChange} className="w-full">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="overview" className="flex items-center gap-2">
                <Shield className="h-4 w-4" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="consistency" className="flex items-center gap-2">
                <Target className="h-4 w-4" />
                Character Consistency
              </TabsTrigger>
              <TabsTrigger value="plot-threads" className="flex items-center gap-2">
                <GitBranch className="h-4 w-4" />
                Plot Threads
              </TabsTrigger>
              <TabsTrigger value="relationships" className="flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Relationships
              </TabsTrigger>
              <TabsTrigger value="flags" className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Flags & Alerts
              </TabsTrigger>
            </TabsList>

            {/* Overview Tab - Original Continuity Dashboard */}
            <TabsContent value="overview" className="mt-6">
              <ContinuityDashboard
                scene_id={(selectedScene as any)._id || selectedScene.id}
                scene_name={selectedScene.name}
                onFlagResolve={handleFlagResolve}
                onCharacterStateUpdate={handleCharacterStateUpdate}
                onEnvironmentStateUpdate={handleEnvironmentStateUpdate}
                onAnalyzeContent={handleAnalyzeContent}
                showRealTimeAlerts={true}
                showFlagManagement={true}
                showCharacterStates={true}
                showEnvironmentStates={true}
                autoRefresh={true}
                refreshInterval={30000}
              />
            </TabsContent>

            {/* Character Consistency Tab */}
            <TabsContent value="consistency" className="mt-6">
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <h2 className="text-xl font-semibold mb-2">Character Consistency Tracking</h2>
                  <p className="text-muted-foreground">
                    Monitor character consistency scores and resolve inconsistencies
                  </p>
                </div>
                
                <CharacterConsistencyScoreDisplay
                  character_id={mockConsistencyData.character_id}
                  character_name={mockConsistencyData.character_name}
                  consistency_score={mockConsistencyData.consistency_score}
                  recent_inconsistencies={mockConsistencyData.recent_inconsistencies}
                  onInconsistencyClick={(inconsistency) => {
                    toast({
                      title: "Viewing Inconsistency",
                      description: `Opening details for: ${inconsistency.description}`,
                    })
                  }}
                />
              </div>
            </TabsContent>

            {/* Plot Threads Tab */}
            <TabsContent value="plot-threads" className="mt-6">
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <h2 className="text-xl font-semibold mb-2">Plot Thread Management</h2>
                  <p className="text-muted-foreground">
                    Create, track, and manage plot threads and story elements
                  </p>
                </div>
                
                <PlotThreadTrackingInterface
                  scene_id={(selectedScene as any)._id || selectedScene.id}
                  threads={mockPlotThreads}
                  onThreadClick={(thread) => {
                    toast({
                      title: "Thread Selected",
                      description: `Viewing: ${thread.thread_name}`,
                    })
                  }}
                  onElementClick={(element) => {
                    toast({
                      title: "Element Selected", 
                      description: `Viewing: ${element.element_name}`,
                    })
                  }}
                  onCreateThread={() => {
                    toast({
                      title: "Thread Created",
                      description: "New plot thread created successfully.",
                    })
                  }}
                  onUpdateThread={(thread) => {
                    toast({
                      title: "Thread Updated",
                      description: `${thread.thread_name} has been updated.`,
                    })
                  }}
                  onDeleteThread={(threadId) => {
                    toast({
                      title: "Thread Deleted",
                      description: "Plot thread has been deleted.",
                    })
                  }}
                  onCreateElement={(threadId) => {
                    toast({
                      title: "Element Created",
                      description: "New plot element created successfully.",
                    })
                  }}
                  onUpdateElement={(element) => {
                    toast({
                      title: "Element Updated",
                      description: `${element.element_name} has been updated.`,
                    })
                  }}
                  onDeleteElement={(elementId) => {
                    toast({
                      title: "Element Deleted",
                      description: "Plot element has been deleted.",
                    })
                  }}
                  compact={false}
                  editable={true}
                />
              </div>
            </TabsContent>

            {/* Relationships Tab */}
            <TabsContent value="relationships" className="mt-6">
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <h2 className="text-xl font-semibold mb-2">Relationship Dynamics</h2>
                  <p className="text-muted-foreground">
                    Visualize and track character relationship evolution over time
                  </p>
                </div>
                
                <RelationshipDynamicsVisualization
                  scene_id={(selectedScene as any)._id || selectedScene.id}
                  character_relationships={mockRelationships}
                  onRelationshipClick={(relationshipId) => {
                    toast({
                      title: "Relationship Selected",
                      description: "Viewing relationship timeline.",
                    })
                  }}
                  compact={false}
                />
              </div>
            </TabsContent>

            {/* Flags & Alerts Tab - Focused continuity management */}
            <TabsContent value="flags" className="mt-6">
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <h2 className="text-xl font-semibold mb-2">Continuity Flags & Alerts</h2>
                  <p className="text-muted-foreground">
                    Manage continuity issues and real-time alerts
                  </p>
                </div>
                
                <ContinuityDashboard
                  scene_id={(selectedScene as any)._id || selectedScene.id}
                  scene_name={selectedScene.name}
                  onFlagResolve={handleFlagResolve}
                  onCharacterStateUpdate={handleCharacterStateUpdate}
                  onEnvironmentStateUpdate={handleEnvironmentStateUpdate}
                  onAnalyzeContent={handleAnalyzeContent}
                  showRealTimeAlerts={true}
                  showFlagManagement={true}
                  showCharacterStates={false}
                  showEnvironmentStates={false}
                  autoRefresh={true}
                  refreshInterval={15000}
                />
              </div>
            </TabsContent>
          </Tabs>
        )}
      </div>
    </div>
  )
} 