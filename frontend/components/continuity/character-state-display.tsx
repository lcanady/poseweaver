"use client"

import { useState, useEffect, useCallback } from 'react'
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
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { 
  Users, 
  Edit, 
  Save, 
  X, 
  Heart, 
  MapPin, 
  Clock, 
  Brain,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronUp,
  History,
  User,
  Activity,
  AlertCircle,
  CheckCircle,
  Plus,
  Minus,
  RefreshCw,
  Loader2
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import { format } from 'date-fns'

import type { 
  CharacterStateDisplayProps, 
  CharacterState, 
  CharacterStateChange 
} from '@/types/continuity'

interface CharacterStateEditorState {
  editingCharacterId: string | null
  editingField: string | null
  editingValue: string
  showHistory: boolean
  showRelationships: boolean
  showPlotKnowledge: boolean
  expandedCharacters: Set<string>
  loading: boolean
  error: string | null
}

const EMOTION_OPTIONS = [
  'Happy', 'Sad', 'Angry', 'Fearful', 'Surprised', 'Disgusted', 'Neutral',
  'Excited', 'Anxious', 'Confident', 'Confused', 'Determined', 'Frustrated'
]

const HEALTH_OPTIONS = [
  'Perfect', 'Good', 'Fair', 'Poor', 'Injured', 'Sick', 'Exhausted', 'Dying'
]

const RELATIONSHIP_TYPES = [
  'Friend', 'Enemy', 'Ally', 'Rival', 'Family', 'Romantic', 'Mentor', 'Student',
  'Neutral', 'Suspicious', 'Trusted', 'Unknown'
]

export function CharacterStateDisplay({
  character_states,
  scene_id,
  editable = false,
  onStateUpdate,
  onHistoryView,
  showRelationships = true,
  showPlotKnowledge = true,
  showHistory = true,
  compactView = false
}: CharacterStateDisplayProps) {
  const [state, setState] = useState<CharacterStateEditorState>({
    editingCharacterId: null,
    editingField: null,
    editingValue: '',
    showHistory: showHistory,
    showRelationships: showRelationships,
    showPlotKnowledge: showPlotKnowledge,
    expandedCharacters: new Set(),
    loading: false,
    error: null
  })

  const { toast } = useToast()

  const handleEdit = useCallback((characterId: string, field: string, currentValue: string) => {
    setState(prev => ({
      ...prev,
      editingCharacterId: characterId,
      editingField: field,
      editingValue: currentValue
    }))
  }, [])

  const handleSave = useCallback(async (characterId: string, field: string, value: string) => {
    if (!onStateUpdate) return

    setState(prev => ({ ...prev, loading: true }))

    try {
      const updates: Partial<CharacterState> = {}
      
      // Parse field path and create nested update object
      const fieldParts = field.split('.')
      if (fieldParts.length === 2) {
        const [category, subField] = fieldParts
        if (category === 'physical_state' || category === 'emotional_state' || category === 'mental_state') {
          updates[category as keyof CharacterState] = {
            ...character_states.find(cs => cs.character_id === characterId)?.[category as keyof CharacterState],
            [subField]: value
          } as any
        }
      } else {
        updates[field as keyof CharacterState] = value as any
      }

      await onStateUpdate(characterId, updates)
      
      setState(prev => ({
        ...prev,
        editingCharacterId: null,
        editingField: null,
        editingValue: '',
        loading: false
      }))

      toast({
        title: "State Updated",
        description: "Character state has been updated successfully.",
        variant: "default",
      })
    } catch (error) {
      setState(prev => ({ ...prev, loading: false }))
      toast({
        title: "Error",
        description: "Failed to update character state. Please try again.",
        variant: "destructive",
      })
    }
  }, [character_states, onStateUpdate, toast])

  const handleCancel = useCallback(() => {
    setState(prev => ({
      ...prev,
      editingCharacterId: null,
      editingField: null,
      editingValue: ''
    }))
  }, [])

  const toggleExpanded = useCallback((characterId: string) => {
    setState(prev => {
      const newExpanded = new Set(prev.expandedCharacters)
      if (newExpanded.has(characterId)) {
        newExpanded.delete(characterId)
      } else {
        newExpanded.add(characterId)
      }
      return { ...prev, expandedCharacters: newExpanded }
    })
  }, [])

  const renderEditableField = useCallback((
    characterId: string,
    field: string,
    value: string,
    label: string,
    type: 'text' | 'textarea' | 'select' = 'text',
    options?: string[]
  ) => {
    const isEditing = state.editingCharacterId === characterId && state.editingField === field
    
    if (isEditing) {
      return (
        <div className="space-y-2">
          <Label className="text-sm font-medium">{label}</Label>
          <div className="flex items-center gap-2">
            {type === 'textarea' ? (
              <Textarea
                value={state.editingValue}
                onChange={(e) => setState(prev => ({ ...prev, editingValue: e.target.value }))}
                className="flex-1"
                rows={2}
              />
            ) : type === 'select' ? (
              <Select
                value={state.editingValue}
                onValueChange={(value) => setState(prev => ({ ...prev, editingValue: value }))}
              >
                <SelectTrigger className="flex-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {options?.map(option => (
                    <SelectItem key={option} value={option}>{option}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <Input
                value={state.editingValue}
                onChange={(e) => setState(prev => ({ ...prev, editingValue: e.target.value }))}
                className="flex-1"
              />
            )}
            <Button
              size="sm"
              onClick={() => handleSave(characterId, field, state.editingValue)}
              disabled={state.loading}
            >
              {state.loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={handleCancel}
              disabled={state.loading}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )
    }

    return (
      <div className="space-y-1">
        <Label className="text-sm font-medium">{label}</Label>
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            {value || 'Not set'}
          </span>
          {editable && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => handleEdit(characterId, field, value)}
              className="h-6 w-6 p-0"
            >
              <Edit className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>
    )
  }, [state, editable, handleEdit, handleSave, handleCancel])

  const renderCharacterState = useCallback((characterState: CharacterState) => {
    const isExpanded = state.expandedCharacters.has(characterState.character_id)
    
    return (
      <Card key={characterState.character_id} className="transition-all duration-200">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Avatar className="h-8 w-8">
                <AvatarFallback>
                  {characterState.character_name.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div>
                <CardTitle className="text-base">{characterState.character_name}</CardTitle>
                <p className="text-sm text-muted-foreground">
                  Last updated: {format(new Date(characterState.last_updated), 'MMM d, h:mm a')}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                <MapPin className="h-3 w-3 mr-1" />
                {characterState.current_location}
              </Badge>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => toggleExpanded(characterState.character_id)}
              >
                {isExpanded ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </CardHeader>

        <Collapsible open={isExpanded} onOpenChange={() => toggleExpanded(characterState.character_id)}>
          <CollapsibleContent>
            <CardContent className="pt-0">
              <Tabs defaultValue="state" className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="state">State</TabsTrigger>
                  {state.showRelationships && (
                    <TabsTrigger value="relationships">
                      Relationships ({characterState.relationships.length})
                    </TabsTrigger>
                  )}
                  {state.showPlotKnowledge && (
                    <TabsTrigger value="plot">Plot Knowledge</TabsTrigger>
                  )}
                  {state.showHistory && (
                    <TabsTrigger value="history">History</TabsTrigger>
                  )}
                </TabsList>

                {/* State Tab */}
                <TabsContent value="state" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Physical State */}
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <Activity className="h-4 w-4" />
                          Physical State
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {renderEditableField(
                          characterState.character_id,
                          'physical_state.health',
                          characterState.physical_state.health,
                          'Health',
                          'select',
                          HEALTH_OPTIONS
                        )}
                        {renderEditableField(
                          characterState.character_id,
                          'physical_state.appearance',
                          characterState.physical_state.appearance || '',
                          'Appearance',
                          'textarea'
                        )}
                        {characterState.physical_state.injuries && characterState.physical_state.injuries.length > 0 && (
                          <div className="space-y-1">
                            <Label className="text-sm font-medium">Injuries</Label>
                            <div className="space-y-1">
                              {characterState.physical_state.injuries.map((injury, index) => (
                                <Badge key={index} variant="destructive" className="text-xs">
                                  {injury}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                        {characterState.physical_state.equipment && characterState.physical_state.equipment.length > 0 && (
                          <div className="space-y-1">
                            <Label className="text-sm font-medium">Equipment</Label>
                            <div className="space-y-1">
                              {characterState.physical_state.equipment.map((item, index) => (
                                <Badge key={index} variant="outline" className="text-xs">
                                  {item}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>

                    {/* Emotional State */}
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <Heart className="h-4 w-4" />
                          Emotional State
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {renderEditableField(
                          characterState.character_id,
                          'emotional_state.primary_emotion',
                          characterState.emotional_state.primary_emotion,
                          'Primary Emotion',
                          'select',
                          EMOTION_OPTIONS
                        )}
                        {renderEditableField(
                          characterState.character_id,
                          'emotional_state.mood',
                          characterState.emotional_state.mood || '',
                          'Mood',
                          'text'
                        )}
                        {characterState.emotional_state.stress_level !== undefined && (
                          <div className="space-y-1">
                            <Label className="text-sm font-medium">Stress Level</Label>
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-gray-200 rounded-full h-2">
                                <div 
                                  className={cn(
                                    "h-2 rounded-full transition-all duration-300",
                                    characterState.emotional_state.stress_level < 30 ? "bg-green-500" :
                                    characterState.emotional_state.stress_level < 70 ? "bg-yellow-500" :
                                    "bg-red-500"
                                  )}
                                  style={{ width: `${characterState.emotional_state.stress_level}%` }}
                                />
                              </div>
                              <span className="text-xs text-muted-foreground">
                                {characterState.emotional_state.stress_level}%
                              </span>
                            </div>
                          </div>
                        )}
                        {characterState.emotional_state.secondary_emotions && characterState.emotional_state.secondary_emotions.length > 0 && (
                          <div className="space-y-1">
                            <Label className="text-sm font-medium">Secondary Emotions</Label>
                            <div className="flex flex-wrap gap-1">
                              {characterState.emotional_state.secondary_emotions.map((emotion, index) => (
                                <Badge key={index} variant="secondary" className="text-xs">
                                  {emotion}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>

                    {/* Mental State */}
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <Brain className="h-4 w-4" />
                          Mental State
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {renderEditableField(
                          characterState.character_id,
                          'mental_state.alertness',
                          characterState.mental_state.alertness || '',
                          'Alertness',
                          'select',
                          ['Sharp', 'Alert', 'Focused', 'Distracted', 'Drowsy', 'Exhausted']
                        )}
                        {renderEditableField(
                          characterState.character_id,
                          'mental_state.focus',
                          characterState.mental_state.focus || '',
                          'Focus',
                          'text'
                        )}
                        {characterState.mental_state.memory_issues && characterState.mental_state.memory_issues.length > 0 && (
                          <div className="space-y-1">
                            <Label className="text-sm font-medium">Memory Issues</Label>
                            <div className="space-y-1">
                              {characterState.mental_state.memory_issues.map((issue, index) => (
                                <Badge key={index} variant="destructive" className="text-xs">
                                  {issue}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                {/* Relationships Tab */}
                {state.showRelationships && (
                  <TabsContent value="relationships" className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {characterState.relationships.map((relationship, index) => (
                        <Card key={index}>
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <User className="h-4 w-4" />
                                <span className="font-medium">{relationship.character_name}</span>
                              </div>
                              <Badge variant="outline" className="text-xs">
                                {relationship.relationship_type}
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground mb-2">
                              {relationship.relationship_status}
                            </p>
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              Last interaction: {format(new Date(relationship.last_interaction), 'MMM d, yyyy')}
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                      {characterState.relationships.length === 0 && (
                        <div className="col-span-2 text-center py-8">
                          <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                          <p className="text-muted-foreground">No relationships recorded yet.</p>
                        </div>
                      )}
                    </div>
                  </TabsContent>
                )}

                {/* Plot Knowledge Tab */}
                {state.showPlotKnowledge && (
                  <TabsContent value="plot" className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm">Known Facts</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            {characterState.plot_knowledge.known_facts.map((fact, index) => (
                              <div key={index} className="flex items-start gap-2">
                                <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                                <span className="text-sm">{fact}</span>
                              </div>
                            ))}
                            {characterState.plot_knowledge.known_facts.length === 0 && (
                              <p className="text-sm text-muted-foreground">No facts known yet.</p>
                            )}
                          </div>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm">Secrets</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            {characterState.plot_knowledge.secrets.map((secret, index) => (
                              <div key={index} className="flex items-start gap-2">
                                <Eye className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                                <span className="text-sm">{secret}</span>
                              </div>
                            ))}
                            {characterState.plot_knowledge.secrets.length === 0 && (
                              <p className="text-sm text-muted-foreground">No secrets known yet.</p>
                            )}
                          </div>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm">Objectives</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            {characterState.plot_knowledge.objectives.map((objective, index) => (
                              <div key={index} className="flex items-start gap-2">
                                <AlertCircle className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                                <span className="text-sm">{objective}</span>
                              </div>
                            ))}
                            {characterState.plot_knowledge.objectives.length === 0 && (
                              <p className="text-sm text-muted-foreground">No objectives set yet.</p>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  </TabsContent>
                )}

                {/* History Tab */}
                {state.showHistory && (
                  <TabsContent value="history" className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-medium">State Changes</h3>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onHistoryView?.(characterState.character_id)}
                      >
                        <History className="h-4 w-4 mr-2" />
                        View Full History
                      </Button>
                    </div>
                    <ScrollArea className="h-48">
                      <div className="space-y-3">
                        {characterState.state_history.slice(0, 10).map((change, index) => (
                          <div key={index} className="flex items-start gap-3 p-3 bg-gray-50 rounded-md">
                            <div className="flex-1">
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-sm font-medium capitalize">
                                  {change.change_type.replace('_', ' ')}
                                </span>
                                <span className="text-xs text-muted-foreground">
                                  {format(new Date(change.timestamp), 'MMM d, h:mm a')}
                                </span>
                              </div>
                              <div className="text-sm text-muted-foreground">
                                <span className="line-through">{change.before_value}</span>
                                <span className="mx-2">→</span>
                                <span className="font-medium">{change.after_value}</span>
                              </div>
                              {change.change_reason && (
                                <p className="text-xs text-muted-foreground mt-1">
                                  {change.change_reason}
                                </p>
                              )}
                            </div>
                            <Badge variant={change.automatic ? "secondary" : "outline"} className="text-xs">
                              {change.automatic ? "Auto" : "Manual"}
                            </Badge>
                          </div>
                        ))}
                        {characterState.state_history.length === 0 && (
                          <div className="text-center py-8">
                            <History className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                            <p className="text-muted-foreground">No state changes recorded yet.</p>
                          </div>
                        )}
                      </div>
                    </ScrollArea>
                  </TabsContent>
                )}
              </Tabs>
            </CardContent>
          </CollapsibleContent>
        </Collapsible>
      </Card>
    )
  }, [state, renderEditableField, toggleExpanded, onHistoryView])

  if (character_states.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Character States</h3>
          <p className="text-muted-foreground">
            Character states will appear here once they are tracked for this scene.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Users className="h-6 w-6 text-primary" />
          <h2 className="text-xl font-semibold">Character States</h2>
          <Badge variant="outline">{character_states.length}</Badge>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setState(prev => ({ ...prev, showRelationships: !prev.showRelationships }))}
          >
            <Heart className="h-4 w-4 mr-2" />
            {state.showRelationships ? 'Hide' : 'Show'} Relationships
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setState(prev => ({ ...prev, showPlotKnowledge: !prev.showPlotKnowledge }))}
          >
            <Brain className="h-4 w-4 mr-2" />
            {state.showPlotKnowledge ? 'Hide' : 'Show'} Plot Knowledge
          </Button>
        </div>
      </div>

      {/* Character States */}
      <div className="space-y-4">
        {character_states.map((characterState) => (
          <div key={characterState.character_id}>
            {renderCharacterState(characterState)}
          </div>
        ))}
      </div>
    </div>
  )
} 