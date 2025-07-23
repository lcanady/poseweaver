"use client"

import { useState, useCallback, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Checkbox } from '@/components/ui/checkbox'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog'
import { 
  Zap, 
  Plus, 
  Edit, 
  Trash2, 
  ChevronDown, 
  ChevronUp, 
  Clock, 
  Users, 
  Target, 
  Play, 
  Pause, 
  CheckCircle, 
  X, 
  Eye, 
  ExternalLink,
  GitBranch,
  Lightbulb,
  Flag,
  Search,
  Filter,
  Archive,
  AlertTriangle,
  Activity,
  Calendar,
  BookOpen,
  FileText
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { format } from 'date-fns'
import { useToast } from '@/hooks/use-toast'

import type { 
  PlotThread, 
  PlotThreadElement, 
  PlotThreadTrackingProps 
} from '@/types/plot-tracking'

interface ThreadDialogState {
  open: boolean
  thread: PlotThread | null
  isNew: boolean
  submitting: boolean
  formData: {
    thread_name: string
    thread_description: string
    importance: 'minor' | 'moderate' | 'major'
    thread_status: 'active' | 'resolved' | 'abandoned' | 'paused'
    parent_thread_id?: string
  }
}

interface ElementDialogState {
  open: boolean
  element: PlotThreadElement | null
  threadId: string | null
  isNew: boolean
  submitting: boolean
  formData: {
    element_name: string
    element_description: string
    element_type: 'event' | 'clue' | 'revelation' | 'decision' | 'consequence' | 'goal'
    status: 'introduced' | 'developing' | 'resolved' | 'abandoned'
  }
}

interface FilterState {
  search: string
  status: string
  importance: string
  showResolved: boolean
}

const THREAD_STATUS_COLORS = {
  active: 'bg-green-100 text-green-800 border-green-200',
  paused: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  resolved: 'bg-blue-100 text-blue-800 border-blue-200',
  abandoned: 'bg-gray-100 text-gray-800 border-gray-200'
}

const THREAD_IMPORTANCE_COLORS = {
  major: 'bg-red-500',
  moderate: 'bg-yellow-500',
  minor: 'bg-blue-500'
}

const ELEMENT_TYPE_ICONS = {
  event: Calendar,
  clue: Search,
  revelation: Lightbulb,
  decision: GitBranch,
  consequence: Target,
  goal: Flag
}

export function PlotThreadTrackingInterface({
  scene_id,
  threads,
  onThreadClick,
  onElementClick,
  onCreateThread,
  onUpdateThread,
  onDeleteThread,
  onCreateElement,
  onUpdateElement,
  onDeleteElement,
  compact = false,
  editable = true
}: PlotThreadTrackingProps) {
  const [threadDialog, setThreadDialog] = useState<ThreadDialogState>({
    open: false,
    thread: null,
    isNew: false,
    submitting: false,
    formData: {
      thread_name: '',
      thread_description: '',
      importance: 'moderate',
      thread_status: 'active'
    }
  })

  const [elementDialog, setElementDialog] = useState<ElementDialogState>({
    open: false,
    element: null,
    threadId: null,
    isNew: false,
    submitting: false,
    formData: {
      element_name: '',
      element_description: '',
      element_type: 'event',
      status: 'introduced'
    }
  })

  const [filters, setFilters] = useState<FilterState>({
    search: '',
    status: 'all',
    importance: 'all',
    showResolved: false
  })

  const [expandedThreads, setExpandedThreads] = useState<Set<string>>(new Set())
  const [selectedThreads, setSelectedThreads] = useState<Set<string>>(new Set())
  
  const { toast } = useToast()

  const handleCreateThread = useCallback(() => {
    setThreadDialog({
      open: true,
      thread: null,
      isNew: true,
      submitting: false,
      formData: {
        thread_name: '',
        thread_description: '',
        importance: 'moderate',
        thread_status: 'active'
      }
    })
  }, [])

  const handleEditThread = useCallback((thread: PlotThread) => {
    setThreadDialog({
      open: true,
      thread,
      isNew: false,
      submitting: false,
      formData: {
        thread_name: thread.thread_name,
        thread_description: thread.thread_description,
        importance: thread.importance,
        thread_status: thread.thread_status,
        parent_thread_id: thread.parent_thread_id
      }
    })
  }, [])

  const handleCreateElement = useCallback((threadId: string) => {
    setElementDialog({
      open: true,
      element: null,
      threadId,
      isNew: true,
      submitting: false,
      formData: {
        element_name: '',
        element_description: '',
        element_type: 'event',
        status: 'introduced'
      }
    })
  }, [])

  const handleEditElement = useCallback((element: PlotThreadElement) => {
    setElementDialog({
      open: true,
      element,
      threadId: element.thread_id,
      isNew: false,
      submitting: false,
      formData: {
        element_name: element.element_name,
        element_description: element.element_description,
        element_type: element.element_type,
        status: element.status
      }
    })
  }, [])

  const submitThread = useCallback(async () => {
    if (!threadDialog.formData.thread_name.trim()) {
      toast({
        title: "Name Required",
        description: "Please provide a thread name.",
        variant: "destructive"
      })
      return
    }

    setThreadDialog(prev => ({ ...prev, submitting: true }))

    try {
      if (threadDialog.isNew) {
        onCreateThread?.()
      } else if (threadDialog.thread) {
        const updatedThread = {
          ...threadDialog.thread,
          ...threadDialog.formData,
          last_updated_timestamp: new Date().toISOString()
        }
        onUpdateThread?.(updatedThread)
      }

      toast({
        title: threadDialog.isNew ? "Thread Created" : "Thread Updated",
        description: `Plot thread "${threadDialog.formData.thread_name}" has been ${threadDialog.isNew ? 'created' : 'updated'}.`,
      })

      setThreadDialog({
        open: false,
        thread: null,
        isNew: false,
        submitting: false,
        formData: {
          thread_name: '',
          thread_description: '',
          importance: 'moderate',
          thread_status: 'active'
        }
      })
    } catch (error) {
      console.error('Error saving thread:', error)
      toast({
        title: "Save Failed",
        description: "Failed to save thread. Please try again.",
        variant: "destructive"
      })
    } finally {
      setThreadDialog(prev => ({ ...prev, submitting: false }))
    }
  }, [threadDialog, onCreateThread, onUpdateThread, toast])

  const submitElement = useCallback(async () => {
    if (!elementDialog.formData.element_name.trim()) {
      toast({
        title: "Name Required",
        description: "Please provide an element name.",
        variant: "destructive"
      })
      return
    }

    setElementDialog(prev => ({ ...prev, submitting: true }))

    try {
      if (elementDialog.isNew && elementDialog.threadId) {
        onCreateElement?.(elementDialog.threadId)
      } else if (elementDialog.element) {
        const updatedElement = {
          ...elementDialog.element,
          ...elementDialog.formData,
          timestamp: new Date().toISOString()
        }
        onUpdateElement?.(updatedElement)
      }

      toast({
        title: elementDialog.isNew ? "Element Created" : "Element Updated",
        description: `Plot element "${elementDialog.formData.element_name}" has been ${elementDialog.isNew ? 'created' : 'updated'}.`,
      })

      setElementDialog({
        open: false,
        element: null,
        threadId: null,
        isNew: false,
        submitting: false,
        formData: {
          element_name: '',
          element_description: '',
          element_type: 'event',
          status: 'introduced'
        }
      })
    } catch (error) {
      console.error('Error saving element:', error)
      toast({
        title: "Save Failed",
        description: "Failed to save element. Please try again.",
        variant: "destructive"
      })
    } finally {
      setElementDialog(prev => ({ ...prev, submitting: false }))
    }
  }, [elementDialog, onCreateElement, onUpdateElement, toast])

  const toggleExpanded = useCallback((threadId: string) => {
    setExpandedThreads(prev => {
      const newSet = new Set(prev)
      if (newSet.has(threadId)) {
        newSet.delete(threadId)
      } else {
        newSet.add(threadId)
      }
      return newSet
    })
  }, [])

  const toggleSelected = useCallback((threadId: string) => {
    setSelectedThreads(prev => {
      const newSet = new Set(prev)
      if (newSet.has(threadId)) {
        newSet.delete(threadId)
      } else {
        newSet.add(threadId)
      }
      return newSet
    })
  }, [])

  const filteredThreads = useMemo(() => {
    return threads.filter(thread => {
      // Search filter
      if (filters.search && !thread.thread_name.toLowerCase().includes(filters.search.toLowerCase()) &&
          !thread.thread_description.toLowerCase().includes(filters.search.toLowerCase())) {
        return false
      }

      // Status filter
      if (filters.status !== 'all' && thread.thread_status !== filters.status) {
        return false
      }

      // Importance filter
      if (filters.importance !== 'all' && thread.importance !== filters.importance) {
        return false
      }

      // Show resolved filter
      if (!filters.showResolved && thread.thread_status === 'resolved') {
        return false
      }

      return true
    })
  }, [threads, filters])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <Play className="h-3 w-3" />
      case 'paused': return <Pause className="h-3 w-3" />
      case 'resolved': return <CheckCircle className="h-3 w-3" />
      case 'abandoned': return <X className="h-3 w-3" />
      default: return <Play className="h-3 w-3" />
    }
  }

  const parentThreads = threads.filter(t => !t.parent_thread_id)

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-bold flex items-center gap-2">
            <GitBranch className="h-5 w-5 text-primary" />
            Plot Thread Tracking
            <Badge variant="outline" className="ml-2">{filteredThreads.length} threads</Badge>
          </CardTitle>
          
          <div className="flex items-center gap-2">
            {editable && (
              <Button onClick={handleCreateThread} size="sm">
                <Plus className="h-4 w-4 mr-2" />
                New Thread
              </Button>
            )}
            {selectedThreads.size > 0 && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete ({selectedThreads.size})
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete Plot Threads</AlertDialogTitle>
                    <AlertDialogDescription>
                      Are you sure you want to delete {selectedThreads.size} plot thread(s)? This action cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={() => {
                      selectedThreads.forEach(threadId => onDeleteThread?.(threadId))
                      setSelectedThreads(new Set())
                      toast({
                        title: "Threads Deleted",
                        description: `${selectedThreads.size} plot thread(s) deleted.`,
                      })
                    }}>
                      Delete
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Filters */}
        <Card className="mb-4">
          <CardContent className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <Label htmlFor="search" className="text-sm">Search</Label>
                <Input
                  id="search"
                  placeholder="Search threads..."
                  value={filters.search}
                  onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="status" className="text-sm">Status</Label>
                <Select value={filters.status} onValueChange={(value) => setFilters(prev => ({ ...prev, status: value }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="paused">Paused</SelectItem>
                    <SelectItem value="resolved">Resolved</SelectItem>
                    <SelectItem value="abandoned">Abandoned</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="importance" className="text-sm">Importance</Label>
                <Select value={filters.importance} onValueChange={(value) => setFilters(prev => ({ ...prev, importance: value }))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Importance</SelectItem>
                    <SelectItem value="major">Major</SelectItem>
                    <SelectItem value="moderate">Moderate</SelectItem>
                    <SelectItem value="minor">Minor</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-end">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="showResolved"
                    checked={filters.showResolved}
                    onCheckedChange={(checked) => setFilters(prev => ({ ...prev, showResolved: !!checked }))}
                  />
                  <Label htmlFor="showResolved" className="text-sm">Show Resolved</Label>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Thread List */}
        {filteredThreads.length > 0 ? (
          <div className="space-y-4">
            {filteredThreads.map((thread) => {
              const isExpanded = expandedThreads.has(thread.thread_id)
              const isSelected = selectedThreads.has(thread.thread_id)
              
              return (
                <Card key={thread.thread_id} className={cn(
                  "transition-all",
                  isSelected && "ring-2 ring-primary"
                )}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3 flex-1">
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={() => toggleSelected(thread.thread_id)}
                        />
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-2">
                            <div 
                              className={cn(
                                "w-3 h-3 rounded-full", 
                                THREAD_IMPORTANCE_COLORS[thread.importance]
                              )} 
                            />
                            <Button
                              variant="ghost"
                              className="p-0 h-auto font-semibold text-left hover:underline"
                              onClick={() => onThreadClick?.(thread)}
                            >
                              {thread.thread_name}
                            </Button>
                            <Badge className={cn("text-xs", THREAD_STATUS_COLORS[thread.thread_status])}>
                              {getStatusIcon(thread.thread_status)}
                              {thread.thread_status}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {thread.importance}
                            </Badge>
                          </div>
                          
                          <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                            {thread.thread_description}
                          </p>
                          
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Users className="h-3 w-3" />
                              {thread.related_characters.length} characters
                            </span>
                            <span className="flex items-center gap-1">
                              <Target className="h-3 w-3" />
                              {thread.thread_elements.length} elements
                            </span>
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {format(new Date(thread.last_updated_timestamp), 'MMM d, yyyy')}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-1">
                        {editable && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEditThread(thread)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <Button variant="ghost" size="sm">
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>Delete Plot Thread</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    Are you sure you want to delete "{thread.thread_name}"? This will also delete all associated elements.
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                                  <AlertDialogAction onClick={() => onDeleteThread?.(thread.thread_id)}>
                                    Delete
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          </>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleExpanded(thread.thread_id)}
                        >
                          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                        </Button>
                      </div>
                    </div>
                    
                    {/* Expanded Content */}
                    {isExpanded && (
                      <div className="mt-4 pt-4 border-t">
                        <Tabs defaultValue="elements" className="w-full">
                          <TabsList className="grid w-full grid-cols-3">
                            <TabsTrigger value="elements">Elements ({thread.thread_elements.length})</TabsTrigger>
                            <TabsTrigger value="characters">Characters ({thread.related_characters.length})</TabsTrigger>
                            <TabsTrigger value="scenes">Scenes ({thread.scenes.length})</TabsTrigger>
                          </TabsList>
                          
                          <TabsContent value="elements" className="space-y-2 mt-4">
                            <div className="flex justify-between items-center">
                              <h4 className="text-sm font-medium">Plot Elements</h4>
                              {editable && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleCreateElement(thread.thread_id)}
                                >
                                  <Plus className="h-3 w-3 mr-1" />
                                  Add Element
                                </Button>
                              )}
                            </div>
                            
                            {thread.thread_elements.length > 0 ? (
                              <div className="space-y-2">
                                {thread.thread_elements.map((element) => {
                                  const IconComponent = ELEMENT_TYPE_ICONS[element.element_type] || Calendar
                                  
                                  return (
                                    <div key={element.element_id} className="flex items-start gap-2 p-2 bg-gray-50 dark:bg-gray-900 rounded-md">
                                      <IconComponent className="h-4 w-4 mt-0.5 text-primary" />
                                      <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                          <Button
                                            variant="ghost"
                                            className="p-0 h-auto text-sm font-medium hover:underline"
                                            onClick={() => onElementClick?.(element)}
                                          >
                                            {element.element_name}
                                          </Button>
                                          <Badge variant="outline" className="text-xs">
                                            {element.element_type}
                                          </Badge>
                                          <Badge variant={element.status === 'resolved' ? 'default' : 'secondary'} className="text-xs">
                                            {element.status}
                                          </Badge>
                                        </div>
                                        <p className="text-xs text-muted-foreground">
                                          {element.element_description}
                                        </p>
                                      </div>
                                      {editable && (
                                        <div className="flex gap-1">
                                          <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => handleEditElement(element)}
                                          >
                                            <Edit className="h-3 w-3" />
                                          </Button>
                                          <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => onDeleteElement?.(element.element_id)}
                                          >
                                            <Trash2 className="h-3 w-3" />
                                          </Button>
                                        </div>
                                      )}
                                    </div>
                                  )
                                })}
                              </div>
                            ) : (
                              <div className="text-center py-4">
                                <FileText className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                                <p className="text-sm text-muted-foreground">No elements added yet</p>
                              </div>
                            )}
                          </TabsContent>
                          
                          <TabsContent value="characters" className="space-y-2 mt-4">
                            {thread.related_characters.length > 0 ? (
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                {thread.related_characters.map((character, index) => (
                                  <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-900 rounded-md">
                                    <Users className="h-4 w-4 text-primary" />
                                    <span className="text-sm font-medium">{character.character_name}</span>
                                    <Badge variant="outline" className="text-xs">
                                      {character.relevance}
                                    </Badge>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="text-center py-4">
                                <Users className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                                <p className="text-sm text-muted-foreground">No characters involved</p>
                              </div>
                            )}
                          </TabsContent>
                          
                          <TabsContent value="scenes" className="space-y-2 mt-4">
                            {thread.scenes.length > 0 ? (
                              <div className="space-y-2">
                                {thread.scenes.map((scene, index) => (
                                  <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-900 rounded-md">
                                    <BookOpen className="h-4 w-4 text-primary" />
                                    <span className="text-sm font-medium flex-1">{scene.scene_name}</span>
                                    <span className="text-xs text-muted-foreground">
                                      {format(new Date(scene.last_activity), 'MMM d')}
                                    </span>
                                    <Button variant="ghost" size="sm">
                                      <ExternalLink className="h-3 w-3" />
                                    </Button>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="text-center py-4">
                                <BookOpen className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                                <p className="text-sm text-muted-foreground">No scenes linked</p>
                              </div>
                            )}
                          </TabsContent>
                        </Tabs>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )
            })}
          </div>
        ) : (
          <div className="text-center py-12">
            <GitBranch className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Plot Threads</h3>
            <p className="text-muted-foreground mb-4">
              {filters.search || filters.status !== 'all' || filters.importance !== 'all' 
                ? "No threads match your current filters."
                : "Start tracking plot threads to maintain story consistency."
              }
            </p>
            {editable && (
              <Button onClick={handleCreateThread}>
                <Plus className="h-4 w-4 mr-2" />
                Create First Thread
              </Button>
            )}
          </div>
        )}
      </CardContent>

      {/* Thread Dialog */}
      <Dialog open={threadDialog.open} onOpenChange={(open) => 
        setThreadDialog(prev => ({ ...prev, open }))
      }>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {threadDialog.isNew ? 'Create Plot Thread' : 'Edit Plot Thread'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="thread-name">Thread Name</Label>
              <Input
                id="thread-name"
                placeholder="Enter thread name..."
                value={threadDialog.formData.thread_name}
                onChange={(e) => setThreadDialog(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, thread_name: e.target.value }
                }))}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="thread-description">Description</Label>
              <Textarea
                id="thread-description"
                placeholder="Describe this plot thread..."
                value={threadDialog.formData.thread_description}
                onChange={(e) => setThreadDialog(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, thread_description: e.target.value }
                }))}
                className="min-h-20"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="importance">Importance</Label>
                <Select value={threadDialog.formData.importance} onValueChange={(value: any) => 
                  setThreadDialog(prev => ({ 
                    ...prev, 
                    formData: { ...prev.formData, importance: value }
                  }))
                }>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="minor">Minor</SelectItem>
                    <SelectItem value="moderate">Moderate</SelectItem>
                    <SelectItem value="major">Major</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <Select value={threadDialog.formData.thread_status} onValueChange={(value: any) => 
                  setThreadDialog(prev => ({ 
                    ...prev, 
                    formData: { ...prev.formData, thread_status: value }
                  }))
                }>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="paused">Paused</SelectItem>
                    <SelectItem value="resolved">Resolved</SelectItem>
                    <SelectItem value="abandoned">Abandoned</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Parent Thread Selection */}
            {parentThreads.length > 0 && (
              <div className="space-y-2">
                <Label htmlFor="parent-thread">Parent Thread (Optional)</Label>
                <Select value={threadDialog.formData.parent_thread_id || ''} onValueChange={(value) => 
                  setThreadDialog(prev => ({ 
                    ...prev, 
                    formData: { ...prev.formData, parent_thread_id: value || undefined }
                  }))
                }>
                  <SelectTrigger>
                    <SelectValue placeholder="Select parent thread..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">No parent thread</SelectItem>
                    {parentThreads.map(thread => (
                      <SelectItem key={thread.thread_id} value={thread.thread_id}>
                        {thread.thread_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setThreadDialog(prev => ({ ...prev, open: false }))}
              disabled={threadDialog.submitting}
            >
              Cancel
            </Button>
            <Button
              onClick={submitThread}
              disabled={!threadDialog.formData.thread_name.trim() || threadDialog.submitting}
            >
              {threadDialog.submitting ? (
                <>
                  <Activity className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  {threadDialog.isNew ? 'Create' : 'Update'}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Element Dialog */}
      <Dialog open={elementDialog.open} onOpenChange={(open) => 
        setElementDialog(prev => ({ ...prev, open }))
      }>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {elementDialog.isNew ? 'Create Plot Element' : 'Edit Plot Element'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="element-name">Element Name</Label>
              <Input
                id="element-name"
                placeholder="Enter element name..."
                value={elementDialog.formData.element_name}
                onChange={(e) => setElementDialog(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, element_name: e.target.value }
                }))}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="element-description">Description</Label>
              <Textarea
                id="element-description"
                placeholder="Describe this plot element..."
                value={elementDialog.formData.element_description}
                onChange={(e) => setElementDialog(prev => ({ 
                  ...prev, 
                  formData: { ...prev.formData, element_description: e.target.value }
                }))}
                className="min-h-20"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="element-type">Type</Label>
                <Select value={elementDialog.formData.element_type} onValueChange={(value: any) => 
                  setElementDialog(prev => ({ 
                    ...prev, 
                    formData: { ...prev.formData, element_type: value }
                  }))
                }>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="event">Event</SelectItem>
                    <SelectItem value="clue">Clue</SelectItem>
                    <SelectItem value="revelation">Revelation</SelectItem>
                    <SelectItem value="decision">Decision</SelectItem>
                    <SelectItem value="consequence">Consequence</SelectItem>
                    <SelectItem value="goal">Goal</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="element-status">Status</Label>
                <Select value={elementDialog.formData.status} onValueChange={(value: any) => 
                  setElementDialog(prev => ({ 
                    ...prev, 
                    formData: { ...prev.formData, status: value }
                  }))
                }>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="introduced">Introduced</SelectItem>
                    <SelectItem value="developing">Developing</SelectItem>
                    <SelectItem value="resolved">Resolved</SelectItem>
                    <SelectItem value="abandoned">Abandoned</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setElementDialog(prev => ({ ...prev, open: false }))}
              disabled={elementDialog.submitting}
            >
              Cancel
            </Button>
            <Button
              onClick={submitElement}
              disabled={!elementDialog.formData.element_name.trim() || elementDialog.submitting}
            >
              {elementDialog.submitting ? (
                <>
                  <Activity className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  {elementDialog.isNew ? 'Create' : 'Update'}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
} 