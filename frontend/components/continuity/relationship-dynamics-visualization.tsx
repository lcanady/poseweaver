"use client"

import { useState, useCallback, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { 
  Users, 
  Heart, 
  ShieldAlert, 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Clock, 
  BarChart3,
  LineChart,
  Zap,
  Shield,
  Flame,
  AlertTriangle,
  CheckCircle,
  User,
  UsersRound,
  Target,
  Calendar,
  Eye,
  GitBranch,
  ArrowUp,
  ArrowDown,
  Minus
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { format, subDays, subWeeks, subMonths } from 'date-fns'

import type { RelationshipDynamicsProps } from '@/types/plot-tracking'

interface TimelinePoint {
  timestamp: string
  trust_level: number
  tension_level: number
  description: string
  event_type: 'positive' | 'negative' | 'neutral'
}

interface VisualizationState {
  selectedRelationship: string | null
  timeRange: '1w' | '1m' | '3m' | '6m' | 'all'
  viewMode: 'graph' | 'timeline' | 'matrix'
  showTrends: boolean
  groupBy: 'character' | 'relationship_type' | 'tension_level'
}

const RELATIONSHIP_ICONS = {
  friend: Heart,
  enemy: ShieldAlert,
  ally: Shield,
  rival: Flame,
  family: UsersRound,
  romantic: Heart,
  neutral: User,
  unknown: User
}

const TENSION_COLORS = {
  low: 'text-green-600 bg-green-100',
  medium: 'text-yellow-600 bg-yellow-100',
  high: 'text-red-600 bg-red-100'
}

const TREND_ICONS = {
  up: ArrowUp,
  down: ArrowDown,
  stable: Minus
}

export function RelationshipDynamicsVisualization({
  scene_id,
  character_relationships,
  onRelationshipClick,
  compact = false
}: RelationshipDynamicsProps) {
  const [vizState, setVizState] = useState<VisualizationState>({
    selectedRelationship: null,
    timeRange: '1m',
    viewMode: 'timeline',
    showTrends: true,
    groupBy: 'character'
  })

  const getTimeRangeDate = useCallback((range: string): Date => {
    const now = new Date()
    switch (range) {
      case '1w': return subWeeks(now, 1)
      case '1m': return subMonths(now, 1)
      case '3m': return subMonths(now, 3)
      case '6m': return subMonths(now, 6)
      default: return subMonths(now, 12) // 'all'
    }
  }, [])

  const filteredRelationships = useMemo(() => {
    const cutoffDate = getTimeRangeDate(vizState.timeRange)
    
    return character_relationships.map(rel => ({
      ...rel,
      dynamics: rel.dynamics.filter(d => 
        vizState.timeRange === 'all' || new Date(d.timestamp) >= cutoffDate
      )
    })).filter(rel => rel.dynamics.length > 0)
  }, [character_relationships, vizState.timeRange, getTimeRangeDate])

  const calculateTrend = useCallback((dynamics: any[]) => {
    if (dynamics.length < 2) return 'stable'
    
    const recent = dynamics.slice(-3) // Last 3 points
    const trustTrend = recent[recent.length - 1].trust_level - recent[0].trust_level
    const tensionTrend = recent[recent.length - 1].tension_level - recent[0].tension_level
    
    const overallTrend = trustTrend - tensionTrend // Higher trust, lower tension = positive
    
    if (overallTrend > 0.5) return 'up'
    if (overallTrend < -0.5) return 'down'
    return 'stable'
  }, [])

  const getTensionLevel = useCallback((tension: number): 'low' | 'medium' | 'high' => {
    if (tension <= 3) return 'low'
    if (tension <= 7) return 'medium'
    return 'high'
  }, [])

  const getRelationshipIcon = useCallback((type: string) => {
    const IconComponent = RELATIONSHIP_ICONS[type.toLowerCase() as keyof typeof RELATIONSHIP_ICONS] || User
    return <IconComponent className="h-4 w-4" />
  }, [])

  const renderTimelineView = useCallback(() => {
    const selectedRel = filteredRelationships.find(rel => rel.relationship_id === vizState.selectedRelationship)
    
    if (!selectedRel) {
      return (
        <div className="text-center py-8">
          <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Select a Relationship</h3>
          <p className="text-muted-foreground">
            Choose a relationship from the list to view its dynamics timeline.
          </p>
        </div>
      )
    }

    const maxTrust = Math.max(...selectedRel.dynamics.map(d => d.trust_level))
    const maxTension = Math.max(...selectedRel.dynamics.map(d => d.tension_level))

    return (
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {getRelationshipIcon(selectedRel.relationship_type)}
            <div>
              <h3 className="font-semibold">
                {selectedRel.character_name} ↔ {selectedRel.related_character_name}
              </h3>
              <p className="text-sm text-muted-foreground">
                {selectedRel.relationship_type} • {selectedRel.dynamics.length} data points
              </p>
            </div>
          </div>
          <Badge variant="outline" className="capitalize">
            {calculateTrend(selectedRel.dynamics)} trend
          </Badge>
        </div>

        {/* Timeline Graph */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Relationship Dynamics Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 relative bg-gradient-to-r from-gray-50 to-white dark:from-gray-900 dark:to-gray-800 rounded-lg p-4">
              {/* Y-axis labels */}
              <div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs text-muted-foreground">
                <span>10</span>
                <span>5</span>
                <span>0</span>
              </div>
              
              {/* Graph area */}
              <div className="ml-6 h-full relative">
                {selectedRel.dynamics.map((dynamic, index) => {
                  const x = (index / (selectedRel.dynamics.length - 1)) * 100
                  const trustY = 100 - (dynamic.trust_level / 10) * 100
                  const tensionY = 100 - (dynamic.tension_level / 10) * 100
                  
                  return (
                    <div key={index}>
                      {/* Trust level point */}
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <div
                              className="absolute w-2 h-2 bg-green-500 rounded-full cursor-pointer hover:scale-150 transition-transform"
                              style={{ left: `${x}%`, top: `${trustY}%` }}
                            />
                          </TooltipTrigger>
                          <TooltipContent>
                            <div className="text-xs">
                              <div className="font-medium">Trust Level: {dynamic.trust_level}/10</div>
                              <div>{format(new Date(dynamic.timestamp), 'MMM d, yyyy')}</div>
                              <div>{dynamic.description}</div>
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                      
                      {/* Tension level point */}
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <div
                              className="absolute w-2 h-2 bg-red-500 rounded-full cursor-pointer hover:scale-150 transition-transform"
                              style={{ left: `${x}%`, top: `${tensionY}%` }}
                            />
                          </TooltipTrigger>
                          <TooltipContent>
                            <div className="text-xs">
                              <div className="font-medium">Tension Level: {dynamic.tension_level}/10</div>
                              <div>{format(new Date(dynamic.timestamp), 'MMM d, yyyy')}</div>
                              <div>{dynamic.description}</div>
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>

                      {/* Connection lines */}
                      {index < selectedRel.dynamics.length - 1 && (
                        <div>
                          {/* Trust line */}
                          <div
                            className="absolute h-px bg-green-300 opacity-60"
                            style={{
                              left: `${x}%`,
                              top: `${trustY}%`,
                              width: `${(100 / (selectedRel.dynamics.length - 1))}%`,
                              transform: `rotate(${Math.atan2(
                                ((selectedRel.dynamics[index + 1].trust_level / 10) * 100 - (dynamic.trust_level / 10) * 100),
                                (100 / (selectedRel.dynamics.length - 1))
                              )}rad)`
                            }}
                          />
                          {/* Tension line */}
                          <div
                            className="absolute h-px bg-red-300 opacity-60"
                            style={{
                              left: `${x}%`,
                              top: `${tensionY}%`,
                              width: `${(100 / (selectedRel.dynamics.length - 1))}%`,
                              transform: `rotate(${Math.atan2(
                                ((selectedRel.dynamics[index + 1].tension_level / 10) * 100 - (dynamic.tension_level / 10) * 100),
                                (100 / (selectedRel.dynamics.length - 1))
                              )}rad)`
                            }}
                          />
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
              
              {/* Legend */}
              <div className="absolute bottom-0 right-0 flex gap-4 text-xs">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                  <span>Trust</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-red-500 rounded-full" />
                  <span>Tension</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Timeline Events */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Recent Events</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-32">
              <div className="space-y-2">
                {selectedRel.dynamics.slice().reverse().map((dynamic, index) => {
                  const trend = index < selectedRel.dynamics.length - 1 
                    ? calculateTrend([selectedRel.dynamics[selectedRel.dynamics.length - index - 2], dynamic])
                    : 'stable'
                  const TrendIcon = TREND_ICONS[trend as keyof typeof TREND_ICONS]
                  
                  return (
                    <div key={index} className="flex items-start gap-3 p-2 bg-gray-50 dark:bg-gray-900 rounded-md">
                      <div className="flex items-center gap-1 mt-1">
                        <TrendIcon className={cn(
                          "h-3 w-3",
                          trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-600'
                        )} />
                        <Badge variant="outline" className="text-xs">
                          T{dynamic.trust_level} R{dynamic.tension_level}
                        </Badge>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-muted-foreground">
                            {format(new Date(dynamic.timestamp), 'MMM d, h:mm a')}
                          </span>
                        </div>
                        <p className="text-sm">{dynamic.description}</p>
                      </div>
                    </div>
                  )
                })}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    )
  }, [filteredRelationships, vizState.selectedRelationship, getRelationshipIcon, calculateTrend])

  const renderMatrixView = useCallback(() => {
    // Group relationships by characters
    const characterMap = new Map<string, any[]>()
    
    filteredRelationships.forEach(rel => {
      if (!characterMap.has(rel.character_name)) {
        characterMap.set(rel.character_name, [])
      }
      characterMap.get(rel.character_name)?.push(rel)
    })

    return (
      <div className="space-y-4">
        <div className="text-center">
          <h3 className="text-lg font-semibold mb-2">Relationship Matrix</h3>
          <p className="text-sm text-muted-foreground">
            Overview of all character relationships and their current dynamics
          </p>
        </div>
        
        <div className="grid gap-4">
          {Array.from(characterMap.entries()).map(([character, relationships]) => (
            <Card key={character}>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <User className="h-4 w-4" />
                  {character}
                  <Badge variant="outline" className="text-xs">{relationships.length} relationships</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {relationships.map(rel => {
                    const latestDynamic = rel.dynamics[rel.dynamics.length - 1]
                    const trend = calculateTrend(rel.dynamics)
                    const TrendIcon = TREND_ICONS[trend as keyof typeof TREND_ICONS]
                    const tensionLevel = getTensionLevel(latestDynamic.tension_level)
                    
                    return (
                      <div
                        key={rel.relationship_id}
                        className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-md cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                        onClick={() => {
                          setVizState(prev => ({ 
                            ...prev, 
                            selectedRelationship: rel.relationship_id,
                            viewMode: 'timeline'
                          }))
                          onRelationshipClick?.(rel.relationship_id)
                        }}
                      >
                        {getRelationshipIcon(rel.relationship_type)}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-sm">{rel.related_character_name}</span>
                            <Badge variant="outline" className="text-xs">
                              {rel.relationship_type}
                            </Badge>
                            <TrendIcon className={cn(
                              "h-3 w-3",
                              trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-600'
                            )} />
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="flex-1">
                              <div className="flex items-center justify-between text-xs mb-1">
                                <span>Trust</span>
                                <span>{latestDynamic.trust_level}/10</span>
                              </div>
                              <Progress value={latestDynamic.trust_level * 10} className="h-1" />
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center justify-between text-xs mb-1">
                                <span>Tension</span>
                                <span>{latestDynamic.tension_level}/10</span>
                              </div>
                              <Progress 
                                value={latestDynamic.tension_level * 10} 
                                className={cn("h-1", TENSION_COLORS[tensionLevel])} 
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }, [filteredRelationships, calculateTrend, getTensionLevel, getRelationshipIcon, onRelationshipClick])

  const renderGraphView = useCallback(() => {
    // Calculate network stats
    const totalRelationships = filteredRelationships.length
    const averageTrust = filteredRelationships.reduce((acc, rel) => {
      const latest = rel.dynamics[rel.dynamics.length - 1]
      return acc + latest.trust_level
    }, 0) / totalRelationships || 0
    
    const averageTension = filteredRelationships.reduce((acc, rel) => {
      const latest = rel.dynamics[rel.dynamics.length - 1]
      return acc + latest.tension_level
    }, 0) / totalRelationships || 0

    const upTrends = filteredRelationships.filter(rel => calculateTrend(rel.dynamics) === 'up').length
    const downTrends = filteredRelationships.filter(rel => calculateTrend(rel.dynamics) === 'down').length

    return (
      <div className="space-y-6">
        {/* Network Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Relationships</p>
                  <p className="text-2xl font-bold">{totalRelationships}</p>
                </div>
                <Users className="h-5 w-5 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Avg Trust</p>
                  <p className="text-2xl font-bold text-green-600">{averageTrust.toFixed(1)}/10</p>
                </div>
                <Heart className="h-5 w-5 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Avg Tension</p>
                  <p className="text-2xl font-bold text-red-600">{averageTension.toFixed(1)}/10</p>
                </div>
                <Zap className="h-5 w-5 text-red-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Trends</p>
                  <p className="text-sm">
                    <span className="text-green-600">↑{upTrends}</span> / 
                    <span className="text-red-600">↓{downTrends}</span>
                  </p>
                </div>
                <TrendingUp className="h-5 w-5 text-blue-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Relationship List */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">All Relationships</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {filteredRelationships.map(rel => {
                const latestDynamic = rel.dynamics[rel.dynamics.length - 1]
                const trend = calculateTrend(rel.dynamics)
                const TrendIcon = TREND_ICONS[trend as keyof typeof TREND_ICONS]
                
                return (
                  <div
                    key={rel.relationship_id}
                    className="flex items-center gap-4 p-3 bg-gray-50 dark:bg-gray-900 rounded-md cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    onClick={() => {
                      setVizState(prev => ({ 
                        ...prev, 
                        selectedRelationship: rel.relationship_id,
                        viewMode: 'timeline'
                      }))
                      onRelationshipClick?.(rel.relationship_id)
                    }}
                  >
                    {getRelationshipIcon(rel.relationship_type)}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium">
                          {rel.character_name} ↔ {rel.related_character_name}
                        </span>
                        <Badge variant="outline" className="text-xs">{rel.relationship_type}</Badge>
                        <TrendIcon className={cn(
                          "h-3 w-3",
                          trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-600'
                        )} />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span>Trust</span>
                            <span>{latestDynamic.trust_level}/10</span>
                          </div>
                          <Progress value={latestDynamic.trust_level * 10} className="h-1" />
                        </div>
                        <div>
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span>Tension</span>
                            <span>{latestDynamic.tension_level}/10</span>
                          </div>
                          <Progress value={latestDynamic.tension_level * 10} className="h-1" />
                        </div>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }, [filteredRelationships, calculateTrend, getRelationshipIcon, onRelationshipClick])

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-bold flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            Relationship Dynamics
            <Badge variant="outline" className="ml-2">
              {filteredRelationships.length} relationships
            </Badge>
          </CardTitle>
          
          <div className="flex items-center gap-2">
            <Select value={vizState.timeRange} onValueChange={(value: any) => 
              setVizState(prev => ({ ...prev, timeRange: value }))
            }>
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1w">1 Week</SelectItem>
                <SelectItem value="1m">1 Month</SelectItem>
                <SelectItem value="3m">3 Months</SelectItem>
                <SelectItem value="6m">6 Months</SelectItem>
                <SelectItem value="all">All Time</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={vizState.viewMode} onValueChange={(value: any) => 
              setVizState(prev => ({ ...prev, viewMode: value }))
            }>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="graph">Overview</SelectItem>
                <SelectItem value="timeline">Timeline</SelectItem>
                <SelectItem value="matrix">Matrix</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {filteredRelationships.length > 0 ? (
          <div>
            {vizState.viewMode === 'timeline' && renderTimelineView()}
            {vizState.viewMode === 'matrix' && renderMatrixView()}
            {vizState.viewMode === 'graph' && renderGraphView()}
          </div>
        ) : (
          <div className="text-center py-12">
            <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Relationship Data</h3>
            <p className="text-muted-foreground">
              No relationship dynamics found for the selected time range.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 