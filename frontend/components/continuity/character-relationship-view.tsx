"use client"

import { useState, useCallback, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Progress } from '@/components/ui/progress'
import {
  Users,
  Heart,
  ShieldAlert,
  Star,
  UserPlus,
  Clock,
  ChevronDown,
  ChevronUp,
  Info,
  Flame,
  Shield,
  AlertCircle,
  User,
  UsersRound,
  ArrowUpDown
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { format } from 'date-fns'

import type { CharacterRelationshipViewProps, CharacterRelationship } from '@/types/character-tracking'

export function CharacterRelationshipView({
  character_id,
  character_name,
  relationships,
  onRelationshipClick,
  onCharacterClick,
  compact = false
}: CharacterRelationshipViewProps) {
  const [expandedRelationships, setExpandedRelationships] = useState<Set<string>>(new Set())
  const [activeTab, setActiveTab] = useState<string>('current')
  const [sortOrder, setSortOrder] = useState<string>('trust') // 'trust', 'familiarity', 'recent'
  
  const toggleExpanded = useCallback((relationshipId: string) => {
    setExpandedRelationships(prev => {
      const newSet = new Set(prev)
      if (newSet.has(relationshipId)) {
        newSet.delete(relationshipId)
      } else {
        newSet.add(relationshipId)
      }
      return newSet
    })
  }, [])

  const sortedRelationships = useMemo(() => {
    return [...relationships].sort((a, b) => {
      switch (sortOrder) {
        case 'trust':
          return b.trust_level - a.trust_level
        case 'familiarity':
          return b.familiarity - a.familiarity
        case 'recent':
          return new Date(b.last_interaction_timestamp).getTime() - 
                 new Date(a.last_interaction_timestamp).getTime()
        default:
          return b.trust_level - a.trust_level
      }
    })
  }, [relationships, sortOrder])

  const getRelationshipBadgeColor = (relationshipType: string): string => {
    switch (relationshipType.toLowerCase()) {
      case 'friend':
        return 'bg-green-500 hover:bg-green-600'
      case 'enemy':
        return 'bg-red-500 hover:bg-red-600'
      case 'ally':
        return 'bg-blue-500 hover:bg-blue-600'
      case 'rival':
        return 'bg-orange-500 hover:bg-orange-600'
      case 'family':
        return 'bg-purple-500 hover:bg-purple-600'
      case 'romantic':
        return 'bg-pink-500 hover:bg-pink-600'
      case 'mentor':
      case 'student':
        return 'bg-yellow-500 hover:bg-yellow-600'
      case 'neutral':
        return 'bg-gray-500 hover:bg-gray-600'
      default:
        return 'bg-gray-500 hover:bg-gray-600'
    }
  }

  const formatDate = (timestamp: string): string => {
    return format(new Date(timestamp), 'MMM d, yyyy')
  }

  const getRelationshipIcon = (relationshipType: string) => {
    switch (relationshipType.toLowerCase()) {
      case 'friend':
        return <Users className="h-4 w-4" />
      case 'enemy':
        return <ShieldAlert className="h-4 w-4" />
      case 'ally':
        return <Shield className="h-4 w-4" />
      case 'rival':
        return <Flame className="h-4 w-4" />
      case 'family':
        return <UsersRound className="h-4 w-4" />
      case 'romantic':
        return <Heart className="h-4 w-4" />
      case 'mentor':
        return <Star className="h-4 w-4" />
      case 'student':
        return <UserPlus className="h-4 w-4" />
      default:
        return <User className="h-4 w-4" />
    }
  }
  
  const getRelationshipStatus = (relationship: CharacterRelationship): React.ReactNode => {
    // Define visualization based on trust and familiarity levels
    const combinedScore = (relationship.trust_level + relationship.familiarity) / 2
    let color = ''
    let statusText = ''
    
    if (combinedScore >= 9) {
      color = 'text-green-500'
      statusText = 'Strong'
    } else if (combinedScore >= 7) {
      color = 'text-blue-500'
      statusText = 'Good'
    } else if (combinedScore >= 5) {
      color = 'text-yellow-500'
      statusText = 'Neutral'
    } else if (combinedScore >= 3) {
      color = 'text-orange-500'
      statusText = 'Strained'
    } else {
      color = 'text-red-500'
      statusText = 'Poor'
    }
    
    return (
      <span className={color + " font-medium"}>{statusText}</span>
    )
  }

  return (
    <Card className={cn("w-full", compact ? "p-2" : "")}>
      <CardHeader className={cn("pb-2", compact ? "p-3" : "")}>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-bold flex items-center gap-2">
            <Users className="h-5 w-5 text-muted-foreground" />
            Character Relationships
            <Badge variant="outline" className="ml-2">
              {character_name || 'Unknown Character'}
            </Badge>
          </CardTitle>
          
          <div className="flex items-center gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSortOrder('trust')}
                    className={cn(sortOrder === 'trust' ? "bg-secondary" : "")}
                  >
                    <Shield className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sort by Trust Level</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSortOrder('familiarity')}
                    className={cn(sortOrder === 'familiarity' ? "bg-secondary" : "")}
                  >
                    <Users className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sort by Familiarity</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSortOrder('recent')}
                    className={cn(sortOrder === 'recent' ? "bg-secondary" : "")}
                  >
                    <Clock className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sort by Recent Interaction</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {sortedRelationships.length > 0 ? (
          <ScrollArea className={cn("pr-4", compact ? "h-[300px]" : "h-[500px]")}>
            <div className="space-y-4">
              {sortedRelationships.map((relationship) => {
                const isExpanded = expandedRelationships.has(relationship.relationship_id)
                const badgeColor = getRelationshipBadgeColor(relationship.relationship_type)
                
                return (
                  <div 
                    key={relationship.relationship_id}
                    className="border rounded-lg p-3 transition-all hover:bg-accent/20"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex gap-3">
                        <Avatar className="h-10 w-10">
                          <AvatarFallback>{relationship.related_character_name.charAt(0)}</AvatarFallback>
                        </Avatar>
                        
                        <div>
                          <div className="flex items-center gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="p-0 h-auto font-medium text-base hover:bg-transparent hover:underline"
                              onClick={() => onCharacterClick && onCharacterClick(relationship.related_character_id)}
                            >
                              {relationship.related_character_name}
                            </Button>
                            <Badge className={cn("text-white", badgeColor)}>
                              <span className="flex items-center gap-1">
                                {getRelationshipIcon(relationship.relationship_type)}
                                {relationship.relationship_type}
                              </span>
                            </Badge>
                          </div>
                          
                          <div className="text-sm text-muted-foreground flex items-center gap-2">
                            <span>Status: {getRelationshipStatus(relationship)}</span>
                            <span>•</span>
                            <span>Last interaction: {formatDate(relationship.last_interaction_timestamp)}</span>
                          </div>
                        </div>
                      </div>
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleExpanded(relationship.relationship_id)}
                      >
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      </Button>
                    </div>
                    
                    {isExpanded && (
                      <div className="mt-4 space-y-3">
                        <div className="grid grid-cols-2 gap-4">
                          {/* Trust Level */}
                          <div className="space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium">Trust Level</span>
                              <span className="text-sm">{relationship.trust_level}/10</span>
                            </div>
                            <Progress value={relationship.trust_level * 10} className="h-2" />
                          </div>
                          
                          {/* Familiarity */}
                          <div className="space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium">Familiarity</span>
                              <span className="text-sm">{relationship.familiarity}/10</span>
                            </div>
                            <Progress value={relationship.familiarity * 10} className="h-2" />
                          </div>
                        </div>
                        
                        {/* Relationship Dynamics */}
                        <div>
                          <h4 className="text-sm font-medium mb-2">Relationship Dynamics</h4>
                          <p className="text-sm text-muted-foreground">
                            {relationship.relationship_dynamics || "No specific relationship dynamics recorded."}
                          </p>
                        </div>
                        
                        {/* Notable Interactions */}
                        {relationship.notable_interactions && relationship.notable_interactions.length > 0 && (
                          <div>
                            <h4 className="text-sm font-medium mb-2">Notable Interactions</h4>
                            <div className="space-y-2">
                              {relationship.notable_interactions.slice(0, 3).map((interaction, idx) => (
                                <div key={idx} className="bg-secondary/20 rounded-md p-2 text-sm">
                                  <div className="flex justify-between items-start">
                                    <span className="font-medium">{formatDate(interaction.timestamp)}</span>
                                    {interaction.scene_id && interaction.pose_id && (
                                      <Button 
                                        variant="ghost" 
                                        size="sm" 
                                        className="h-6 px-2 text-xs"
                                        onClick={() => onRelationshipClick && onRelationshipClick(relationship)}
                                      >
                                        View
                                      </Button>
                                    )}
                                  </div>
                                  <p className="text-muted-foreground mt-1">{interaction.description}</p>
                                </div>
                              ))}
                              
                              {relationship.notable_interactions.length > 3 && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="w-full text-center text-xs mt-1"
                                  onClick={() => onRelationshipClick && onRelationshipClick(relationship)}
                                >
                                  View {relationship.notable_interactions.length - 3} more interactions
                                </Button>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </ScrollArea>
        ) : (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <AlertCircle className="h-8 w-8 text-muted-foreground mb-2" />
            <h3 className="font-medium text-lg">No relationships found</h3>
            <p className="text-muted-foreground mt-1">
              This character doesn't have any recorded relationships yet.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
