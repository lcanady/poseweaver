"use client"

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import { Input } from '@/components/ui/input'
import { 
  Plus, 
  FileText, 
  Search, 
  Clock, 
  BookOpen, 
  Users, 
  Settings,
  Loader2,
  AlertCircle,
  CheckCircle,
  Archive,
  Trash2,
  Download,
  RefreshCw,
  Edit,
  Eye,
  Calendar,
  TrendingUp,
  Filter
} from 'lucide-react'
import { cn } from '../../lib/utils'

// Import scene management components
import { SceneCreationForm } from './scene-creation-form'
import { SceneHistoryTimeline } from './scene-history-timeline'
import { SceneSearchInterface } from './scene-search-interface'
import { SceneSummaryDisplay } from './scene-summary-display'

import type { 
  Scene, 
  SceneCreationData, 
  SceneManagementDashboardProps, 
  SceneManagementOptions, 
  SceneExportOptions,
  TimelineEvent,
  SceneSummary,
  SummaryGenerationOptions,
  SceneSearchResult
} from '@/types/scene'

interface DashboardState {
  activeTab: string
  selectedScene: Scene | null
  showCreateDialog: boolean
  showEditDialog: boolean
  showDeleteDialog: boolean
  showExportDialog: boolean
  loading: boolean
  error: string | null
  searchResults: SceneSearchResult[]
}

const DEFAULT_MANAGEMENT_OPTIONS: SceneManagementOptions = {
  allow_editing: true,
  allow_archiving: true,
  allow_deletion: true,
  allow_participant_management: true,
  allow_summary_generation: true,
  allow_export: true,
  show_analytics: true,
  show_timeline: true,
  show_search: true
}

export function SceneManagementDashboard({
  scenes,
  onSceneCreate,
  onSceneEdit,
  onSceneArchive,
  onSceneDelete,
  onSceneExport,
  options = DEFAULT_MANAGEMENT_OPTIONS,
  loading = false,
  error
}: SceneManagementDashboardProps) {
  const [dashboardState, setDashboardState] = useState<DashboardState>({
    activeTab: 'overview',
    selectedScene: null,
    showCreateDialog: false,
    showEditDialog: false,
    showDeleteDialog: false,
    showExportDialog: false,
    loading: false,
    error: null,
    searchResults: []
  })

  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([])
  const [sceneSummaries, setSceneSummaries] = useState<{ [sceneId: string]: SceneSummary }>({})
  const [filteredScenes, setFilteredScenes] = useState<Scene[]>(scenes)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'name' | 'updated_at' | 'created_at' | 'pose_count'>('updated_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'completed' | 'archived'>('all')

  // Load timeline events for selected scene
  useEffect(() => {
    if (dashboardState.selectedScene && options.show_timeline) {
      loadTimelineEvents(dashboardState.selectedScene.id)
    }
  }, [dashboardState.selectedScene, options.show_timeline])

  // Load scene summaries
  useEffect(() => {
    if (options.allow_summary_generation) {
      loadSceneSummaries()
    }
  }, [scenes, options.allow_summary_generation])

  // Filter and sort scenes
  useEffect(() => {
    let filtered = [...scenes]

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(scene =>
        scene.name.toLowerCase().includes(query) ||
        scene.description.toLowerCase().includes(query) ||
        scene.participants.some(p => p.character_name.toLowerCase().includes(query))
      )
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(scene => {
        switch (statusFilter) {
          case 'active':
            return scene.is_active
          case 'completed':
            return !scene.is_active && scene.status === 'Completed'
          case 'archived':
            return scene.status === 'Archived'
          default:
            return true
        }
      })
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: any, bValue: any
      
      switch (sortBy) {
        case 'name':
          aValue = a.name.toLowerCase()
          bValue = b.name.toLowerCase()
          break
        case 'updated_at':
          aValue = new Date(a.updated_at).getTime()
          bValue = new Date(b.updated_at).getTime()
          break
        case 'created_at':
          aValue = new Date(a.created_at).getTime()
          bValue = new Date(b.created_at).getTime()
          break
        case 'pose_count':
          aValue = a.poses.length
          bValue = b.poses.length
          break
        default:
          aValue = new Date(a.updated_at).getTime()
          bValue = new Date(b.updated_at).getTime()
      }

      if (sortOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0
      }
    })

    setFilteredScenes(filtered)
  }, [scenes, searchQuery, sortBy, sortOrder, statusFilter])

  const loadTimelineEvents = useCallback(async (sceneId: string) => {
    try {
      const response = await fetch(`/api/search-summary/search/timeline?scene_id=${sceneId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setTimelineEvents(data.data || [])
        }
      }
    } catch (error) {
      console.error('Failed to load timeline events:', error)
    }
  }, [])

  const loadSceneSummaries = useCallback(async () => {
    try {
      const summaryPromises = scenes.map(async (scene) => {
        const response = await fetch(`/api/search-summary/summaries/scenes/${scene.id}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            focus: 'comprehensive',
            max_length: 300
          })
        })

        if (response.ok) {
          const data = await response.json()
          if (data.success) {
            return { sceneId: scene.id, summary: data.data }
          }
        }
        return null
      })

      const summaries = await Promise.all(summaryPromises)
      const summaryMap: { [sceneId: string]: SceneSummary } = {}
      
      summaries.forEach(result => {
        if (result) {
          summaryMap[result.sceneId] = result.summary
        }
      })

      setSceneSummaries(summaryMap)
    } catch (error) {
      console.error('Failed to load scene summaries:', error)
    }
  }, [scenes])

  const handleSceneCreate = useCallback(async (data: SceneCreationData) => {
    if (!onSceneCreate) return

    setDashboardState(prev => ({ ...prev, loading: true, error: null }))

    try {
      await onSceneCreate(data)
      setDashboardState(prev => ({ ...prev, showCreateDialog: false, loading: false }))
    } catch (error) {
      setDashboardState(prev => ({ 
        ...prev, 
        loading: false, 
        error: error instanceof Error ? error.message : 'Failed to create scene'
      }))
    }
  }, [onSceneCreate])

  const handleSceneEdit = useCallback(async (sceneId: string, data: Partial<SceneCreationData>) => {
    if (!onSceneEdit) return

    setDashboardState(prev => ({ ...prev, loading: true, error: null }))

    try {
      await onSceneEdit(sceneId, data)
      setDashboardState(prev => ({ ...prev, showEditDialog: false, loading: false }))
    } catch (error) {
      setDashboardState(prev => ({ 
        ...prev, 
        loading: false, 
        error: error instanceof Error ? error.message : 'Failed to edit scene'
      }))
    }
  }, [onSceneEdit])

  const handleSceneArchive = useCallback(async (sceneId: string) => {
    if (!onSceneArchive) return

    setDashboardState(prev => ({ ...prev, loading: true, error: null }))

    try {
      await onSceneArchive(sceneId)
      setDashboardState(prev => ({ ...prev, loading: false }))
    } catch (error) {
      setDashboardState(prev => ({ 
        ...prev, 
        loading: false, 
        error: error instanceof Error ? error.message : 'Failed to archive scene'
      }))
    }
  }, [onSceneArchive])

  const handleSceneDelete = useCallback(async (sceneId: string) => {
    if (!onSceneDelete) return

    setDashboardState(prev => ({ ...prev, loading: true, error: null }))

    try {
      await onSceneDelete(sceneId)
      setDashboardState(prev => ({ ...prev, showDeleteDialog: false, loading: false }))
    } catch (error) {
      setDashboardState(prev => ({ 
        ...prev, 
        loading: false, 
        error: error instanceof Error ? error.message : 'Failed to delete scene'
      }))
    }
  }, [onSceneDelete])

  const handleSceneExport = useCallback(async (sceneId: string, exportOptions: SceneExportOptions) => {
    if (!onSceneExport) return

    try {
      await onSceneExport(sceneId, exportOptions)
      setDashboardState(prev => ({ ...prev, showExportDialog: false }))
    } catch (error) {
      setDashboardState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Failed to export scene'
      }))
    }
  }, [onSceneExport])

  const handleSummaryEdit = useCallback(async (summaryId: string, newText: string) => {
    try {
      const response = await fetch(`/api/search-summary/summaries/${summaryId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ summary_text: newText })
      })

      if (!response.ok) {
        throw new Error('Failed to update summary')
      }

      // Refresh summaries
      loadSceneSummaries()
    } catch (error) {
      console.error('Failed to edit summary:', error)
      throw error
    }
  }, [loadSceneSummaries])

  const handleSummaryRegenerate = useCallback(async (sceneId: string, options: SummaryGenerationOptions) => {
    try {
      const response = await fetch(`/api/search-summary/summaries/scenes/${sceneId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(options)
      })

      if (!response.ok) {
        throw new Error('Failed to regenerate summary')
      }

      // Refresh summaries
      loadSceneSummaries()
    } catch (error) {
      console.error('Failed to regenerate summary:', error)
      throw error
    }
  }, [loadSceneSummaries])

  const handleSearchResults = useCallback((results: SceneSearchResult[]) => {
    setDashboardState(prev => ({ ...prev, searchResults: results }))
  }, [])

  const getSceneStatusColor = (scene: Scene) => {
    if (scene.is_active) return 'bg-green-100 text-green-800'
    if (scene.status === 'Completed') return 'bg-blue-100 text-blue-800'
    if (scene.status === 'Archived') return 'bg-gray-100 text-gray-800'
    return 'bg-gray-100 text-gray-800'
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleDateString()
  }

  const getSceneStats = () => {
    const total = scenes.length
    const active = scenes.filter(s => s.is_active).length
    const completed = scenes.filter(s => s.status === 'Completed').length
    const archived = scenes.filter(s => s.status === 'Archived').length
    const totalPoses = scenes.reduce((sum, s) => sum + s.poses.length, 0)

    return { total, active, completed, archived, totalPoses }
  }

  const stats = getSceneStats()

  return (
    <div className="space-y-6">
      {/* Dashboard Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Scene Management Dashboard
            </CardTitle>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadSceneSummaries()}
                disabled={loading}
              >
                <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
              </Button>
              <Button
                onClick={() => setDashboardState(prev => ({ ...prev, showCreateDialog: true }))}
                disabled={loading}
              >
                <Plus className="h-4 w-4 mr-2" />
                New Scene
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Stats Overview */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.total}</div>
              <div className="text-sm text-muted-foreground">Total Scenes</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{stats.active}</div>
              <div className="text-sm text-muted-foreground">Active</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{stats.completed}</div>
              <div className="text-sm text-muted-foreground">Completed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">{stats.archived}</div>
              <div className="text-sm text-muted-foreground">Archived</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{stats.totalPoses}</div>
              <div className="text-sm text-muted-foreground">Total Poses</div>
            </div>
          </div>

          {/* Error Display */}
          {(error || dashboardState.error) && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error || dashboardState.error}</AlertDescription>
            </Alert>
          )}

          {/* Search and Filter Controls */}
          <div className="flex flex-wrap gap-2 mb-4">
            <div className="flex-1 min-w-[200px]">
              <Input
                placeholder="Search scenes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full"
              />
            </div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-3 py-2 border rounded-md"
            >
              <option value="updated_at">Updated</option>
              <option value="created_at">Created</option>
              <option value="name">Name</option>
              <option value="pose_count">Poses</option>
            </select>
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value as any)}
              className="px-3 py-2 border rounded-md"
            >
              <option value="desc">Desc</option>
              <option value="asc">Asc</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="px-3 py-2 border rounded-md"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
              <option value="archived">Archived</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs 
        value={dashboardState.activeTab} 
        onValueChange={(value) => setDashboardState(prev => ({ ...prev, activeTab: value }))}
      >
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="timeline" disabled={!options.show_timeline}>Timeline</TabsTrigger>
          <TabsTrigger value="search" disabled={!options.show_search}>Search</TabsTrigger>
          <TabsTrigger value="summaries" disabled={!options.allow_summary_generation}>Summaries</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : filteredScenes.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No scenes found</h3>
              <p className="text-muted-foreground mb-4">
                {searchQuery ? 'No scenes match your search criteria.' : 'Get started by creating your first scene.'}
              </p>
              <Button onClick={() => setDashboardState(prev => ({ ...prev, showCreateDialog: true }))}>
                <Plus className="h-4 w-4 mr-2" />
                Create Scene
              </Button>
            </div>
          ) : (
            <div className="grid gap-4">
              {filteredScenes.map((scene) => (
                <Card key={scene.id} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <CardTitle className="text-lg">{scene.name}</CardTitle>
                        <Badge variant="outline" className={getSceneStatusColor(scene)}>
                          {scene.status}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setDashboardState(prev => ({ ...prev, selectedScene: scene, activeTab: 'timeline' }))}
                        >
                          <Clock className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setDashboardState(prev => ({ ...prev, selectedScene: scene, showEditDialog: true }))}
                          disabled={!options.allow_editing}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleSceneArchive(scene.id)}
                          disabled={!options.allow_archiving}
                        >
                          <Archive className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setDashboardState(prev => ({ ...prev, selectedScene: scene, showDeleteDialog: true }))}
                          disabled={!options.allow_deletion}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">{scene.description}</p>
                    <div className="flex items-center gap-6 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Users className="h-4 w-4" />
                        {scene.participants.length} participants
                      </div>
                      <div className="flex items-center gap-1">
                        <FileText className="h-4 w-4" />
                        {scene.poses.length} poses
                      </div>
                      <div className="flex items-center gap-1">
                        <Calendar className="h-4 w-4" />
                        {formatTimestamp(scene.updated_at)}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Timeline Tab */}
        <TabsContent value="timeline">
          {dashboardState.selectedScene ? (
            <SceneHistoryTimeline
              scene={dashboardState.selectedScene}
              events={timelineEvents}
              onPoseClick={(poseId) => console.log('Pose clicked:', poseId)}
              onCharacterClick={(characterId) => console.log('Character clicked:', characterId)}
              showFilters={true}
              showSearch={true}
              groupByDate={true}
            />
          ) : (
            <div className="text-center py-8">
              <Clock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Select a Scene</h3>
              <p className="text-muted-foreground">
                Choose a scene from the overview to view its timeline.
              </p>
            </div>
          )}
        </TabsContent>

        {/* Search Tab */}
        <TabsContent value="search">
          <SceneSearchInterface
            onSearchResults={handleSearchResults}
            showAdvancedFilters={true}
            showExportOptions={true}
            placeholder="Search scenes, poses, and characters..."
            maxResults={50}
          />
        </TabsContent>

        {/* Summaries Tab */}
        <TabsContent value="summaries">
          <div className="space-y-4">
            {Object.entries(sceneSummaries).map(([sceneId, summary]) => (
              <SceneSummaryDisplay
                key={sceneId}
                summary={summary}
                onEdit={handleSummaryEdit}
                onRegenerate={handleSummaryRegenerate}
                onExport={async (summary) => {
                  // Handle export
                  console.log('Export summary:', summary)
                }}
                editable={true}
                showMetadata={true}
                showRegenerateOptions={true}
              />
            ))}
            {Object.keys(sceneSummaries).length === 0 && (
              <div className="text-center py-8">
                <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Summaries</h3>
                <p className="text-muted-foreground">
                  Scene summaries will appear here once they are generated.
                </p>
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* Scene Creation Dialog */}
      <Dialog open={dashboardState.showCreateDialog} onOpenChange={(open) => setDashboardState(prev => ({ ...prev, showCreateDialog: open }))}>
        <DialogContent className="sm:max-w-4xl">
          <DialogHeader>
            <DialogTitle>Create New Scene</DialogTitle>
          </DialogHeader>
          <SceneCreationForm
            onSubmit={handleSceneCreate}
            onCancel={() => setDashboardState(prev => ({ ...prev, showCreateDialog: false }))}
            loading={dashboardState.loading}
            error={dashboardState.error||undefined}
          />
        </DialogContent>
      </Dialog>

      {/* Scene Edit Dialog */}
      <Dialog open={dashboardState.showEditDialog} onOpenChange={(open) => setDashboardState(prev => ({ ...prev, showEditDialog: open }))}>
        <DialogContent className="sm:max-w-4xl">
          <DialogHeader>
            <DialogTitle>Edit Scene</DialogTitle>
          </DialogHeader>
          {dashboardState.selectedScene && (
            <SceneCreationForm
              onSubmit={(data) => handleSceneEdit(dashboardState.selectedScene!.id, data)}
              onCancel={() => setDashboardState(prev => ({ ...prev, showEditDialog: false }))}
              initialData={{
                name: dashboardState.selectedScene.name,
                description: dashboardState.selectedScene.description,
                tags: dashboardState.selectedScene.tags,
                participants: dashboardState.selectedScene.participants.map(p => ({
                  character_id: p.character_id,
                  character_name: p.character_name
                }))
              }}
              isEditing={true}
              loading={dashboardState.loading}
              error={dashboardState.error || undefined}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Scene Delete Dialog */}
      <Dialog open={dashboardState.showDeleteDialog} onOpenChange={(open) => setDashboardState(prev => ({ ...prev, showDeleteDialog: open }))}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Scene</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Are you sure you want to delete "{dashboardState.selectedScene?.name}"? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setDashboardState(prev => ({ ...prev, showDeleteDialog: false }))}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={() => dashboardState.selectedScene && handleSceneDelete(dashboardState.selectedScene.id)}
                disabled={dashboardState.loading}
              >
                {dashboardState.loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Trash2 className="h-4 w-4 mr-2" />}
                Delete
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
} 