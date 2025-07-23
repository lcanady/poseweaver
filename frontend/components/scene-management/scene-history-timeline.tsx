"use client"

import { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { 
  Clock, 
  User, 
  Search, 
  Filter, 
  Calendar, 
  Users, 
  MessageSquare, 
  Activity, 
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Eye,
  Copy,
  ExternalLink,
  Loader2,
  AlertCircle
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Scene, TimelineEvent, SceneTimelineProps } from '@/types/scene'

interface TimelineFilters {
  search?: string
  character?: string
  poseType?: string
  dateRange?: {
    start: string
    end: string
  }
  eventTypes?: string[]
}

interface TimelineViewOptions {
  groupByDate: boolean
  showWordCounts: boolean
  showSentiment: boolean
  showOOC: boolean
  highlightCharacter?: string
  density: 'compact' | 'normal' | 'detailed'
}

export function SceneHistoryTimeline({ 
  scene, 
  events, 
  onPoseClick, 
  onCharacterClick, 
  showFilters = true,
  showSearch = true,
  groupByDate = true,
  highlightCharacter 
}: SceneTimelineProps) {
  const [filters, setFilters] = useState<TimelineFilters>({})
  const [viewOptions, setViewOptions] = useState<TimelineViewOptions>({
    groupByDate: groupByDate,
    showWordCounts: true,
    showSentiment: false,
    showOOC: false,
    highlightCharacter: highlightCharacter,
    density: 'normal'
  })
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null)
  const [currentPage, setCurrentPage] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const eventsPerPage = 50

  // Filter and sort events
  const filteredEvents = useMemo(() => {
    let filtered = [...events]

    // Apply search filter
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase()
      filtered = filtered.filter(event => 
        event.title.toLowerCase().includes(searchTerm) ||
        event.description.toLowerCase().includes(searchTerm) ||
        event.character_name?.toLowerCase().includes(searchTerm) ||
        event.pose_text?.toLowerCase().includes(searchTerm)
      )
    }

    // Apply character filter
    if (filters.character) {
      filtered = filtered.filter(event => 
        event.character_name === filters.character
      )
    }

    // Apply pose type filter
    if (filters.poseType) {
      filtered = filtered.filter(event => 
        event.pose_type === filters.poseType
      )
    }

    // Apply date range filter
    if (filters.dateRange) {
      const start = new Date(filters.dateRange.start)
      const end = new Date(filters.dateRange.end)
      filtered = filtered.filter(event => {
        const eventDate = new Date(event.timestamp)
        return eventDate >= start && eventDate <= end
      })
    }

    // Apply event type filter
    if (filters.eventTypes && filters.eventTypes.length > 0) {
      filtered = filtered.filter(event => 
        filters.eventTypes!.includes(event.type)
      )
    }

    // Filter out OOC if not showing them
    if (!viewOptions.showOOC) {
      filtered = filtered.filter(event => 
        !event.metadata?.is_ooc
      )
    }

    return filtered.sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )
  }, [events, filters, viewOptions.showOOC])

  // Group events by date if requested
  const groupedEvents = useMemo(() => {
    if (!viewOptions.groupByDate) {
      return { ungrouped: filteredEvents }
    }

    const groups: { [key: string]: TimelineEvent[] } = {}
    filteredEvents.forEach(event => {
      const date = new Date(event.timestamp).toDateString()
      if (!groups[date]) {
        groups[date] = []
      }
      groups[date].push(event)
    })

    return groups
  }, [filteredEvents, viewOptions.groupByDate])

  // Get paginated events
  const paginatedEvents = useMemo(() => {
    const start = currentPage * eventsPerPage
    const end = start + eventsPerPage

    if (viewOptions.groupByDate) {
      const groupEntries = Object.entries(groupedEvents)
      const paginatedGroups: { [key: string]: TimelineEvent[] } = {}
      
      let currentCount = 0
      for (const [date, events] of groupEntries) {
        const remainingSlots = eventsPerPage - currentCount
        if (remainingSlots <= 0) break
        
        paginatedGroups[date] = events.slice(0, remainingSlots)
        currentCount += events.length
      }
      
      return paginatedGroups
    } else {
      return { ungrouped: filteredEvents.slice(start, end) }
    }
  }, [groupedEvents, currentPage, eventsPerPage, viewOptions.groupByDate, filteredEvents])

  // Get unique characters for filtering
  const characters = useMemo(() => {
    const uniqueCharacters = new Set<string>()
    events.forEach(event => {
      if (event.character_name) {
        uniqueCharacters.add(event.character_name)
      }
    })
    return Array.from(uniqueCharacters).sort()
  }, [events])

  // Get unique pose types for filtering
  const poseTypes = useMemo(() => {
    const uniqueTypes = new Set<string>()
    events.forEach(event => {
      if (event.pose_type) {
        uniqueTypes.add(event.pose_type)
      }
    })
    return Array.from(uniqueTypes).sort()
  }, [events])

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleString()
  }

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'pose':
        return <MessageSquare className="h-4 w-4" />
      case 'character_join':
        return <Users className="h-4 w-4" />
      case 'character_leave':
        return <User className="h-4 w-4" />
      case 'scene_start':
        return <Activity className="h-4 w-4" />
      case 'scene_end':
        return <BookOpen className="h-4 w-4" />
      case 'summary_generated':
        return <Clock className="h-4 w-4" />
      default:
        return <Clock className="h-4 w-4" />
    }
  }

  const getEventColor = (type: string) => {
    switch (type) {
      case 'pose':
        return 'bg-blue-500'
      case 'character_join':
        return 'bg-green-500'
      case 'character_leave':
        return 'bg-orange-500'
      case 'scene_start':
        return 'bg-purple-500'
      case 'scene_end':
        return 'bg-red-500'
      case 'summary_generated':
        return 'bg-gray-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getPoseTypeColor = (type: string) => {
    switch (type) {
      case 'action':
        return 'bg-blue-100 text-blue-800'
      case 'dialogue':
        return 'bg-green-100 text-green-800'
      case 'internal':
        return 'bg-purple-100 text-purple-800'
      case 'ooc':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return 'bg-green-100 text-green-800'
      case 'negative':
        return 'bg-red-100 text-red-800'
      case 'neutral':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const copyEventText = (event: TimelineEvent) => {
    const text = event.pose_text || event.description
    navigator.clipboard.writeText(text)
  }

  const handleEventClick = (event: TimelineEvent) => {
    if (event.type === 'pose' && onPoseClick) {
      onPoseClick(event.id)
    }
    setSelectedEvent(event)
  }

  const handleCharacterClick = (characterName: string) => {
    if (onCharacterClick) {
      // Find character ID - this would need to be provided or looked up
      onCharacterClick(characterName)
    }
    setViewOptions(prev => ({
      ...prev,
      highlightCharacter: prev.highlightCharacter === characterName ? undefined : characterName
    }))
  }

  const totalEvents = filteredEvents.length
  const totalPages = Math.ceil(totalEvents / eventsPerPage)
  const hasNextPage = currentPage < totalPages - 1
  const hasPrevPage = currentPage > 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Scene Timeline
          </CardTitle>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>{totalEvents} events</span>
            <span>•</span>
            <span>{scene.participants.length} participants</span>
            <span>•</span>
            <span>Created {new Date(scene.created_at).toLocaleDateString()}</span>
          </div>
        </CardHeader>
      </Card>

      {/* Filters and Controls */}
      {showFilters && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Filters & Options</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="filters" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="filters">Filters</TabsTrigger>
                <TabsTrigger value="options">View Options</TabsTrigger>
              </TabsList>
              
              <TabsContent value="filters" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {showSearch && (
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Search</label>
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                          placeholder="Search events..."
                          className="pl-10"
                          value={filters.search || ''}
                          onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                        />
                      </div>
                    </div>
                  )}

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Character</label>
                    <Select
                      value={filters.character || 'all'}
                      onValueChange={(value) => setFilters(prev => ({ ...prev, character: value === 'all' ? undefined : value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="All characters" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All characters</SelectItem>
                        {characters.map(character => (
                          <SelectItem key={character} value={character}>
                            {character}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Pose Type</label>
                    <Select
                      value={filters.poseType || 'all'}
                      onValueChange={(value) => setFilters(prev => ({ ...prev, poseType: value === 'all' ? undefined : value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="All types" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All types</SelectItem>
                        {poseTypes.map(type => (
                          <SelectItem key={type} value={type}>
                            {type}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setFilters({})}
                  >
                    Clear Filters
                  </Button>
                  <Badge variant="secondary">
                    {totalEvents} events
                  </Badge>
                </div>
              </TabsContent>

              <TabsContent value="options" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">View Density</label>
                    <Select
                      value={viewOptions.density}
                      onValueChange={(value: any) => setViewOptions(prev => ({ ...prev, density: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="compact">Compact</SelectItem>
                        <SelectItem value="normal">Normal</SelectItem>
                        <SelectItem value="detailed">Detailed</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Group By</label>
                    <Select
                      value={viewOptions.groupByDate ? 'date' : 'none'}
                      onValueChange={(value) => setViewOptions(prev => ({ ...prev, groupByDate: value === 'date' }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">None</SelectItem>
                        <SelectItem value="date">Date</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex flex-wrap gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={viewOptions.showWordCounts}
                      onChange={(e) => setViewOptions(prev => ({ ...prev, showWordCounts: e.target.checked }))}
                    />
                    <span className="text-sm">Show word counts</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={viewOptions.showSentiment}
                      onChange={(e) => setViewOptions(prev => ({ ...prev, showSentiment: e.target.checked }))}
                    />
                    <span className="text-sm">Show sentiment</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={viewOptions.showOOC}
                      onChange={(e) => setViewOptions(prev => ({ ...prev, showOOC: e.target.checked }))}
                    />
                    <span className="text-sm">Show OOC</span>
                  </label>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* Timeline Events */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Timeline Events</CardTitle>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.max(0, prev - 1))}
                disabled={!hasPrevPage}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {currentPage + 1} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.min(totalPages - 1, prev + 1))}
                disabled={!hasNextPage}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-8">
              <AlertCircle className="h-6 w-6 text-red-500 mr-2" />
              <span className="text-red-500">{error}</span>
            </div>
          ) : totalEvents === 0 ? (
            <div className="text-center py-8">
              <Clock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No events found</h3>
              <p className="text-muted-foreground">
                Try adjusting your filters or search criteria.
              </p>
            </div>
          ) : (
            <ScrollArea className="h-[600px]">
              <div className="space-y-6">
                {Object.entries(paginatedEvents).map(([groupKey, groupEvents]) => (
                  <div key={groupKey} className="space-y-4">
                    {groupKey !== 'ungrouped' && viewOptions.groupByDate && (
                      <div className="flex items-center gap-2 sticky top-0 bg-background py-2 border-b">
                        <Calendar className="h-4 w-4" />
                        <h3 className="font-semibold text-lg">{groupKey}</h3>
                        <Badge variant="outline">{groupEvents.length} events</Badge>
                      </div>
                    )}
                    
                    <div className="space-y-4">
                      {groupEvents.map((event, index) => (
                        <div
                          key={event.id}
                          className={cn(
                            "flex gap-4 p-4 border rounded-lg cursor-pointer hover:bg-accent/50 transition-colors",
                            viewOptions.highlightCharacter === event.character_name && "ring-2 ring-primary",
                            viewOptions.density === 'compact' && "p-3",
                            viewOptions.density === 'detailed' && "p-6"
                          )}
                          onClick={() => handleEventClick(event)}
                        >
                          {/* Timeline indicator */}
                          <div className="flex flex-col items-center">
                            <div className={cn(
                              "w-8 h-8 rounded-full flex items-center justify-center text-white",
                              getEventColor(event.type)
                            )}>
                              {getEventIcon(event.type)}
                            </div>
                            {index < groupEvents.length - 1 && (
                              <div className="w-px h-6 bg-border mt-2" />
                            )}
                          </div>

                          {/* Event content */}
                          <div className="flex-1 space-y-2">
                            <div className="flex items-center gap-2">
                              <h4 className="font-medium">{event.title}</h4>
                              {event.character_name && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 px-2"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleCharacterClick(event.character_name!)
                                  }}
                                >
                                  <User className="h-3 w-3 mr-1" />
                                  {event.character_name}
                                </Button>
                              )}
                              {event.pose_type && (
                                <Badge variant="outline" className={getPoseTypeColor(event.pose_type)}>
                                  {event.pose_type}
                                </Badge>
                              )}
                              {viewOptions.showSentiment && event.metadata?.sentiment && (
                                <Badge variant="outline" className={getSentimentColor(event.metadata.sentiment)}>
                                  {event.metadata.sentiment}
                                </Badge>
                              )}
                            </div>

                            <p className="text-sm text-muted-foreground">
                              {formatTimestamp(event.timestamp)}
                            </p>

                            {viewOptions.density !== 'compact' && (
                              <p className="text-sm">
                                {event.description.length > 200 && viewOptions.density === 'normal'
                                  ? `${event.description.substring(0, 200)}...`
                                  : event.description}
                              </p>
                            )}

                            {viewOptions.density === 'detailed' && event.pose_text && (
                              <div className="mt-2 p-2 bg-muted rounded text-sm">
                                <p className="font-medium mb-1">Pose Text:</p>
                                <p>{event.pose_text}</p>
                              </div>
                            )}

                            {/* Metadata */}
                            {viewOptions.density !== 'compact' && (
                              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                {viewOptions.showWordCounts && event.metadata?.word_count && (
                                  <span>{event.metadata.word_count} words</span>
                                )}
                                {event.metadata?.is_ooc && (
                                  <Badge variant="outline" className="text-xs">OOC</Badge>
                                )}
                                {event.metadata?.plot_significance && (
                                  <span>Plot: {(event.metadata.plot_significance * 100).toFixed(0)}%</span>
                                )}
                              </div>
                            )}
                          </div>

                          {/* Action buttons */}
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation()
                                copyEventText(event)
                              }}
                            >
                              <Copy className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation()
                                setSelectedEvent(event)
                              }}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      {/* Event Detail Dialog */}
      <Dialog open={!!selectedEvent} onOpenChange={() => setSelectedEvent(null)}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedEvent && getEventIcon(selectedEvent.type)}
              {selectedEvent?.title}
            </DialogTitle>
          </DialogHeader>
          {selectedEvent && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">Type:</span> {selectedEvent.type}
                </div>
                <div>
                  <span className="font-medium">Time:</span> {formatTimestamp(selectedEvent.timestamp)}
                </div>
                {selectedEvent.character_name && (
                  <div>
                    <span className="font-medium">Character:</span> {selectedEvent.character_name}
                  </div>
                )}
                {selectedEvent.pose_type && (
                  <div>
                    <span className="font-medium">Pose Type:</span> {selectedEvent.pose_type}
                  </div>
                )}
              </div>
              
              <Separator />
              
              <div>
                <h4 className="font-medium mb-2">Description</h4>
                <p className="text-sm">{selectedEvent.description}</p>
              </div>
              
              {selectedEvent.pose_text && (
                <div>
                  <h4 className="font-medium mb-2">Pose Text</h4>
                  <div className="bg-muted p-3 rounded text-sm">
                    <p>{selectedEvent.pose_text}</p>
                  </div>
                </div>
              )}
              
              {selectedEvent.metadata && (
                <div>
                  <h4 className="font-medium mb-2">Metadata</h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {selectedEvent.metadata.word_count && (
                      <div>Word count: {selectedEvent.metadata.word_count}</div>
                    )}
                    {selectedEvent.metadata.sentiment && (
                      <div>Sentiment: {selectedEvent.metadata.sentiment}</div>
                    )}
                    {selectedEvent.metadata.plot_significance && (
                      <div>Plot significance: {(selectedEvent.metadata.plot_significance * 100).toFixed(0)}%</div>
                    )}
                    {selectedEvent.metadata.is_ooc && (
                      <div>OOC: Yes</div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
} 