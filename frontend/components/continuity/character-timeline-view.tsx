"use client"

import { useState, useCallback, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import {
  Clock,
  User,
  Heart,
  Brain,
  Activity,
  MapPin,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Eye,
  AlertCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { format } from 'date-fns'

import type { CharacterTimelineViewProps, CharacterTimelineEntry } from '@/types/character-tracking'

const MAX_SNIPPET_LENGTH = 120

export function CharacterTimelineView({
  character_id,
  scene_id,
  timelineEntries,
  onEntryClick,
  onPoseView,
  showPoseSnippets = true,
  compact = false,
  maxEntries = 20
}: CharacterTimelineViewProps) {
  const [expandedEntries, setExpandedEntries] = useState<Set<string>>(new Set())
  const [activeTab, setActiveTab] = useState<string>('timeline')
  const [filter, setFilter] = useState<string>('all') // 'all', 'emotional', 'physical', 'mental'

  // Filter entries by character if character_id is provided
  const filteredEntries = useMemo(() => {
    let entries = [...timelineEntries]
    
    // Filter by character if specified
    if (character_id) {
      entries = entries.filter(entry => entry.character_id === character_id)
    }
    
    // Filter by state change type if not 'all'
    if (filter !== 'all') {
      entries = entries.filter(entry => {
        const prevIndex = timelineEntries.findIndex(e => e.timestamp === entry.timestamp) - 1
        if (prevIndex < 0) return true
        
        const prevEntry = timelineEntries[prevIndex]
        
        // Check if there are changes in the specific state type
        if (filter === 'emotional' && JSON.stringify(entry.state_snapshot.emotional_state) !== 
            JSON.stringify(prevEntry.state_snapshot.emotional_state)) {
          return true
        }
        if (filter === 'physical' && JSON.stringify(entry.state_snapshot.physical_state) !== 
            JSON.stringify(prevEntry.state_snapshot.physical_state)) {
          return true
        }
        if (filter === 'mental' && JSON.stringify(entry.state_snapshot.mental_state) !== 
            JSON.stringify(prevEntry.state_snapshot.mental_state)) {
          return true
        }
        
        return false
      })
    }
    
    // Sort by timestamp (most recent first)
    entries.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    
    // Limit to maxEntries
    return entries.slice(0, maxEntries)
  }, [timelineEntries, character_id, filter, maxEntries])

  const toggleExpanded = useCallback((entryId: string) => {
    setExpandedEntries(prev => {
      const newSet = new Set(prev)
      if (newSet.has(entryId)) {
        newSet.delete(entryId)
      } else {
        newSet.add(entryId)
      }
      return newSet
    })
  }, [])

  const formatTime = (timestamp: string): string => {
    return format(new Date(timestamp), 'MMM d, yyyy h:mm a')
  }
  
  const getStateChangeSummary = (entry: CharacterTimelineEntry): string => {
    const prevIndex = timelineEntries.findIndex(e => e.timestamp === entry.timestamp) - 1
    if (prevIndex < 0) return 'Initial state recorded'
    
    const prevEntry = timelineEntries[prevIndex]
    const changes: string[] = []
    
    // Check for emotional state changes
    if (JSON.stringify(entry.state_snapshot.emotional_state) !== 
        JSON.stringify(prevEntry.state_snapshot.emotional_state)) {
      changes.push('Emotional state changed')
    }
    
    // Check for physical state changes
    if (JSON.stringify(entry.state_snapshot.physical_state) !== 
        JSON.stringify(prevEntry.state_snapshot.physical_state)) {
      changes.push('Physical state changed')
    }
    
    // Check for mental state changes
    if (JSON.stringify(entry.state_snapshot.mental_state) !== 
        JSON.stringify(prevEntry.state_snapshot.mental_state)) {
      changes.push('Mental state changed')
    }
    
    return changes.length > 0 ? changes.join(', ') : 'No significant changes'
  }

  const getChangeBadgeColor = (type: string): string => {
    switch (type) {
      case 'emotional':
        return 'bg-pink-500 hover:bg-pink-600'
      case 'physical':
        return 'bg-blue-500 hover:bg-blue-600'
      case 'mental':
        return 'bg-purple-500 hover:bg-purple-600'
      default:
        return 'bg-gray-500 hover:bg-gray-600'
    }
  }

  return (
    <Card className={cn("w-full", compact ? "p-2" : "")}>
      <CardHeader className={cn("pb-2", compact ? "p-3" : "")}>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-bold flex items-center gap-2">
            <Clock className="h-5 w-5 text-muted-foreground" />
            Character Timeline
            {character_id && (
              <Badge variant="outline" className="ml-2">
                {timelineEntries.find(entry => entry.character_id === character_id)?.character_name || 'Unknown Character'}
              </Badge>
            )}
          </CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setFilter('all')} 
              className={cn(filter === 'all' ? "bg-secondary" : "")}>
              All
            </Button>
            <Button variant="outline" size="sm" onClick={() => setFilter('emotional')} 
              className={cn(filter === 'emotional' ? "bg-secondary" : "")}>
              <Heart className="h-4 w-4 mr-1" /> Emotional
            </Button>
            <Button variant="outline" size="sm" onClick={() => setFilter('physical')} 
              className={cn(filter === 'physical' ? "bg-secondary" : "")}>
              <Activity className="h-4 w-4 mr-1" /> Physical
            </Button>
            <Button variant="outline" size="sm" onClick={() => setFilter('mental')} 
              className={cn(filter === 'mental' ? "bg-secondary" : "")}>
              <Brain className="h-4 w-4 mr-1" /> Mental
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {filteredEntries.length > 0 ? (
          <ScrollArea className={cn("pr-4", compact ? "h-[300px]" : "h-[500px]")}>
            <div className="space-y-4">
              {filteredEntries.map((entry, index) => {
                const isExpanded = expandedEntries.has(`${entry.character_id}-${entry.timestamp}`)
                const changeSummary = getStateChangeSummary(entry)
                
                return (
                  <div 
                    key={`${entry.character_id}-${entry.timestamp}`}
                    className="relative border rounded-lg p-3 transition-all hover:bg-accent/20"
                  >
                    {/* Timeline connector */}
                    {index < filteredEntries.length - 1 && (
                      <div className="absolute left-7 top-12 bottom-0 w-0.5 bg-border" />
                    )}
                    
                    <div className="flex gap-3">
                      <Avatar className="h-10 w-10">
                        <AvatarFallback>{entry.character_name.charAt(0)}</AvatarFallback>
                      </Avatar>
                      
                      <div className="flex-1">
                        <div className="flex justify-between items-start mb-1">
                          <div>
                            <div className="font-medium">{entry.character_name}</div>
                            <div className="text-sm text-muted-foreground">{formatTime(entry.timestamp)}</div>
                          </div>
                          
                          <div className="flex gap-2">
                            {changeSummary.includes('Emotional') && (
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger>
                                    <Badge variant="secondary" className={cn(getChangeBadgeColor('emotional'), "text-white")}>
                                      <Heart className="h-3 w-3 mr-1" />
                                    </Badge>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p>Emotional state changed</p>
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                            )}
                            
                            {changeSummary.includes('Physical') && (
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger>
                                    <Badge variant="secondary" className={cn(getChangeBadgeColor('physical'), "text-white")}>
                                      <Activity className="h-3 w-3 mr-1" />
                                    </Badge>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p>Physical state changed</p>
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                            )}
                            
                            {changeSummary.includes('Mental') && (
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger>
                                    <Badge variant="secondary" className={cn(getChangeBadgeColor('mental'), "text-white")}>
                                      <Brain className="h-3 w-3 mr-1" />
                                    </Badge>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p>Mental state changed</p>
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                            )}
                          </div>
                        </div>
                        
                        {showPoseSnippets && entry.pose_snippet && (
                          <div className="text-sm text-muted-foreground my-2 italic">
                            "{entry.pose_snippet.length > MAX_SNIPPET_LENGTH && !isExpanded
                              ? `${entry.pose_snippet.substring(0, MAX_SNIPPET_LENGTH)}...`
                              : entry.pose_snippet}"
                          </div>
                        )}
                        
                        <div className="mt-2 flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => toggleExpanded(`${entry.character_id}-${entry.timestamp}`)}
                          >
                            {isExpanded ? (
                              <>
                                <ChevronUp className="h-4 w-4 mr-1" /> Hide Details
                              </>
                            ) : (
                              <>
                                <ChevronDown className="h-4 w-4 mr-1" /> Show Details
                              </>
                            )}
                          </Button>
                          
                          {entry.pose_id && onPoseView && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => onPoseView(entry.pose_id!)}
                            >
                              <Eye className="h-4 w-4 mr-1" /> View Pose
                            </Button>
                          )}
                        </div>
                        
                        {isExpanded && (
                          <div className="mt-3 p-3 bg-secondary/20 rounded-md space-y-3">
                            {/* Emotional State */}
                            <div>
                              <h4 className="text-sm font-medium flex items-center gap-1 mb-1">
                                <Heart className="h-4 w-4 text-pink-500" /> Emotional State
                              </h4>
                              <div className="grid grid-cols-2 gap-2 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Mood:</span>
                                  <span>{entry.state_snapshot.emotional_state?.mood || 'Unknown'}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Stress Level:</span>
                                  <span>{entry.state_snapshot.emotional_state?.stress_level || 'Unknown'}</span>
                                </div>
                              </div>
                            </div>
                            
                            {/* Physical State */}
                            <div>
                              <h4 className="text-sm font-medium flex items-center gap-1 mb-1">
                                <Activity className="h-4 w-4 text-blue-500" /> Physical State
                              </h4>
                              <div className="grid grid-cols-2 gap-2 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Health:</span>
                                  <span>{entry.state_snapshot.physical_state?.health || 'Unknown'}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Energy:</span>
                                  <span>{entry.state_snapshot.physical_state?.energy || 'Unknown'}</span>
                                </div>
                                {entry.state_snapshot.physical_state?.injuries && (
                                  <div className="col-span-2 flex justify-between">
                                    <span className="text-muted-foreground">Injuries:</span>
                                    <span>{entry.state_snapshot.physical_state.injuries}</span>
                                  </div>
                                )}
                              </div>
                            </div>
                            
                            {/* Mental State */}
                            <div>
                              <h4 className="text-sm font-medium flex items-center gap-1 mb-1">
                                <Brain className="h-4 w-4 text-purple-500" /> Mental State
                              </h4>
                              <div className="grid grid-cols-2 gap-2 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Focus:</span>
                                  <span>{entry.state_snapshot.mental_state?.focus || 'Unknown'}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Clarity:</span>
                                  <span>{entry.state_snapshot.mental_state?.clarity || 'Unknown'}</span>
                                </div>
                              </div>
                            </div>
                            
                            {/* Location */}
                            {entry.state_snapshot.location && (
                              <div>
                                <h4 className="text-sm font-medium flex items-center gap-1 mb-1">
                                  <MapPin className="h-4 w-4 text-red-500" /> Location
                                </h4>
                                <div className="text-sm">
                                  {entry.state_snapshot.location}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </ScrollArea>
        ) : (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <AlertCircle className="h-8 w-8 text-muted-foreground mb-2" />
            <h3 className="font-medium text-lg">No timeline entries found</h3>
            <p className="text-muted-foreground mt-1">
              {character_id 
                ? "This character doesn't have any recorded state changes yet."
                : "There are no character state changes recorded for this scene."}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
