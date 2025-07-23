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
import { 
  MapPin, 
  Edit, 
  Save, 
  X, 
  Sun, 
  Cloud, 
  CloudRain,
  Snowflake,
  Wind,
  Thermometer,
  Volume2,
  Flower,
  Clock,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronUp,
  History,
  Users,
  Settings,
  Lightbulb,
  Waves,
  Mountain,
  Building,
  Trees,
  Home,
  Plus,
  Minus,
  RefreshCw,
  Loader2,
  AlertCircle,
  CheckCircle
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import { format } from 'date-fns'

import type { 
  EnvironmentStateDisplayProps, 
  EnvironmentState, 
  EnvironmentStateChange 
} from '@/types/continuity'

interface EnvironmentEditorState {
  editingEnvironmentId: string | null
  editingField: string | null
  editingValue: string
  showInteractiveElements: boolean
  showOccupants: boolean
  showHistory: boolean
  expandedEnvironments: Set<string>
  loading: boolean
  error: string | null
}

const LOCATION_TYPES = [
  'Indoor', 'Outdoor', 'Urban', 'Rural', 'Natural', 'Supernatural', 'Vehicle', 'Structure'
]

const LIGHTING_OPTIONS = [
  'Bright sunlight', 'Daylight', 'Overcast', 'Twilight', 'Moonlight', 'Starlight', 
  'Artificial lighting', 'Candlelight', 'Firelight', 'Darkness', 'Magical lighting'
]

const WEATHER_OPTIONS = [
  'Clear', 'Partly cloudy', 'Cloudy', 'Overcast', 'Light rain', 'Heavy rain', 
  'Drizzle', 'Thunderstorm', 'Snow', 'Blizzard', 'Fog', 'Mist', 'Windy', 'Calm'
]

const TEMPERATURE_OPTIONS = [
  'Freezing', 'Cold', 'Cool', 'Mild', 'Warm', 'Hot', 'Sweltering'
]

const TIME_OPTIONS = [
  'Dawn', 'Morning', 'Late morning', 'Midday', 'Afternoon', 'Late afternoon', 
  'Evening', 'Dusk', 'Night', 'Late night', 'Midnight', 'Pre-dawn'
]

export function EnvironmentStateDisplay({
  environment_states,
  scene_id,
  editable = false,
  onStateUpdate,
  onHistoryView,
  showInteractiveElements = true,
  showOccupants = true,
  showHistory = true,
  compactView = false
}: EnvironmentStateDisplayProps) {
  const [state, setState] = useState<EnvironmentEditorState>({
    editingEnvironmentId: null,
    editingField: null,
    editingValue: '',
    showInteractiveElements: showInteractiveElements,
    showOccupants: showOccupants,
    showHistory: showHistory,
    expandedEnvironments: new Set(),
    loading: false,
    error: null
  })

  const { toast } = useToast()

  const handleEdit = useCallback((environmentId: string, field: string, currentValue: string) => {
    setState(prev => ({
      ...prev,
      editingEnvironmentId: environmentId,
      editingField: field,
      editingValue: currentValue
    }))
  }, [])

  const handleSave = useCallback(async (environmentId: string, field: string, value: string) => {
    if (!onStateUpdate) return

    setState(prev => ({ ...prev, loading: true }))

    try {
      const updates: Partial<EnvironmentState> = {}
      
      // Parse field path and create nested update object
      const fieldParts = field.split('.')
      if (fieldParts.length === 2) {
        const [category, subField] = fieldParts
        if (category === 'atmospheric_conditions' || category === 'temporal_markers') {
          updates[category as keyof EnvironmentState] = {
            ...environment_states.find(es => es.id === environmentId)?.[category as keyof EnvironmentState],
            [subField]: value
          } as any
        }
      } else {
        updates[field as keyof EnvironmentState] = value as any
      }

      await onStateUpdate(environmentId, updates)
      
      setState(prev => ({
        ...prev,
        editingEnvironmentId: null,
        editingField: null,
        editingValue: '',
        loading: false
      }))

      toast({
        title: "Environment Updated",
        description: "Environment state has been updated successfully.",
        variant: "default",
      })
    } catch (error) {
      setState(prev => ({ ...prev, loading: false }))
      toast({
        title: "Error",
        description: "Failed to update environment state. Please try again.",
        variant: "destructive",
      })
    }
  }, [environment_states, onStateUpdate, toast])

  const handleCancel = useCallback(() => {
    setState(prev => ({
      ...prev,
      editingEnvironmentId: null,
      editingField: null,
      editingValue: ''
    }))
  }, [])

  const toggleExpanded = useCallback((environmentId: string) => {
    setState(prev => {
      const newExpanded = new Set(prev.expandedEnvironments)
      if (newExpanded.has(environmentId)) {
        newExpanded.delete(environmentId)
      } else {
        newExpanded.add(environmentId)
      }
      return { ...prev, expandedEnvironments: newExpanded }
    })
  }, [])

  const renderEditableField = useCallback((
    environmentId: string,
    field: string,
    value: string,
    label: string,
    type: 'text' | 'textarea' | 'select' = 'text',
    options?: string[]
  ) => {
    const isEditing = state.editingEnvironmentId === environmentId && state.editingField === field
    
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
                rows={3}
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
              onClick={() => handleSave(environmentId, field, state.editingValue)}
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
              onClick={() => handleEdit(environmentId, field, value)}
              className="h-6 w-6 p-0"
            >
              <Edit className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>
    )
  }, [state, editable, handleEdit, handleSave, handleCancel])

  const getLocationIcon = (locationType: string) => {
    switch (locationType.toLowerCase()) {
      case 'indoor':
        return <Home className="h-4 w-4" />
      case 'outdoor':
        return <Trees className="h-4 w-4" />
      case 'urban':
        return <Building className="h-4 w-4" />
      case 'natural':
        return <Mountain className="h-4 w-4" />
      case 'structure':
        return <Building className="h-4 w-4" />
      default:
        return <MapPin className="h-4 w-4" />
    }
  }

  const getWeatherIcon = (weather: string) => {
    const weatherLower = weather.toLowerCase()
    if (weatherLower.includes('rain') || weatherLower.includes('drizzle')) {
      return <CloudRain className="h-4 w-4" />
    }
    if (weatherLower.includes('snow') || weatherLower.includes('blizzard')) {
      return <Snowflake className="h-4 w-4" />
    }
    if (weatherLower.includes('cloud') || weatherLower.includes('overcast')) {
      return <Cloud className="h-4 w-4" />
    }
    if (weatherLower.includes('wind')) {
      return <Wind className="h-4 w-4" />
    }
    if (weatherLower.includes('clear') || weatherLower.includes('sunny')) {
      return <Sun className="h-4 w-4" />
    }
    return <Sun className="h-4 w-4" />
  }

  const renderEnvironmentState = useCallback((environmentState: EnvironmentState) => {
    const isExpanded = state.expandedEnvironments.has(environmentState.id)
    
    return (
      <Card key={environmentState.id} className="transition-all duration-200">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {getLocationIcon(environmentState.location_type)}
              <div>
                <CardTitle className="text-base">{environmentState.location_name}</CardTitle>
                <p className="text-sm text-muted-foreground">
                  {environmentState.location_type} • Last updated: {format(new Date(environmentState.last_updated), 'MMM d, h:mm a')}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                <Users className="h-3 w-3 mr-1" />
                {environmentState.occupants.length}
              </Badge>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => toggleExpanded(environmentState.id)}
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

        <Collapsible open={isExpanded} onOpenChange={() => toggleExpanded(environmentState.id)}>
          <CollapsibleContent>
            <CardContent className="pt-0">
              <Tabs defaultValue="description" className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="description">Description</TabsTrigger>
                  <TabsTrigger value="conditions">Conditions</TabsTrigger>
                  {state.showInteractiveElements && (
                    <TabsTrigger value="elements">
                      Elements ({environmentState.interactive_elements.length})
                    </TabsTrigger>
                  )}
                  {state.showHistory && (
                    <TabsTrigger value="history">History</TabsTrigger>
                  )}
                </TabsList>

                {/* Description Tab */}
                <TabsContent value="description" className="space-y-4">
                  <Card>
                    <CardContent className="p-4">
                      {renderEditableField(
                        environmentState.id,
                        'physical_description',
                        environmentState.physical_description,
                        'Physical Description',
                        'textarea'
                      )}
                    </CardContent>
                  </Card>

                  {state.showOccupants && (
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <Users className="h-4 w-4" />
                          Current Occupants
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex flex-wrap gap-2">
                          {environmentState.occupants.map((occupant, index) => (
                            <Badge key={index} variant="secondary" className="text-xs">
                              {occupant}
                            </Badge>
                          ))}
                          {environmentState.occupants.length === 0 && (
                            <p className="text-sm text-muted-foreground">No occupants present</p>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </TabsContent>

                {/* Conditions Tab */}
                <TabsContent value="conditions" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Atmospheric Conditions */}
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <Cloud className="h-4 w-4" />
                          Atmospheric Conditions
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {renderEditableField(
                          environmentState.id,
                          'atmospheric_conditions.lighting',
                          environmentState.atmospheric_conditions.lighting,
                          'Lighting',
                          'select',
                          LIGHTING_OPTIONS
                        )}
                        {renderEditableField(
                          environmentState.id,
                          'atmospheric_conditions.weather',
                          environmentState.atmospheric_conditions.weather || '',
                          'Weather',
                          'select',
                          WEATHER_OPTIONS
                        )}
                        {renderEditableField(
                          environmentState.id,
                          'atmospheric_conditions.temperature',
                          environmentState.atmospheric_conditions.temperature || '',
                          'Temperature',
                          'select',
                          TEMPERATURE_OPTIONS
                        )}
                        
                        {environmentState.atmospheric_conditions.sounds && environmentState.atmospheric_conditions.sounds.length > 0 && (
                          <div className="space-y-1">
                            <Label className="text-sm font-medium">Sounds</Label>
                            <div className="flex flex-wrap gap-1">
                              {environmentState.atmospheric_conditions.sounds.map((sound, index) => (
                                <Badge key={index} variant="outline" className="text-xs">
                                  <Volume2 className="h-3 w-3 mr-1" />
                                  {sound}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {environmentState.atmospheric_conditions.scents && environmentState.atmospheric_conditions.scents.length > 0 && (
                          <div className="space-y-1">
                            <Label className="text-sm font-medium">Scents</Label>
                            <div className="flex flex-wrap gap-1">
                              {environmentState.atmospheric_conditions.scents.map((scent, index) => (
                                <Badge key={index} variant="outline" className="text-xs">
                                  <Flower className="h-3 w-3 mr-1" />
                                  {scent}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>

                    {/* Temporal Markers */}
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <Clock className="h-4 w-4" />
                          Temporal Markers
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {renderEditableField(
                          environmentState.id,
                          'temporal_markers.time_of_day',
                          environmentState.temporal_markers.time_of_day,
                          'Time of Day',
                          'select',
                          TIME_OPTIONS
                        )}
                        {renderEditableField(
                          environmentState.id,
                          'temporal_markers.season',
                          environmentState.temporal_markers.season || '',
                          'Season',
                          'select',
                          ['Spring', 'Summer', 'Autumn', 'Winter']
                        )}
                        
                        {environmentState.temporal_markers.special_events && environmentState.temporal_markers.special_events.length > 0 && (
                          <div className="space-y-1">
                            <Label className="text-sm font-medium">Special Events</Label>
                            <div className="space-y-1">
                              {environmentState.temporal_markers.special_events.map((event, index) => (
                                <Badge key={index} variant="secondary" className="text-xs">
                                  {event}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                {/* Interactive Elements Tab */}
                {state.showInteractiveElements && (
                  <TabsContent value="elements" className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {environmentState.interactive_elements.map((element, index) => (
                        <Card key={index}>
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <Settings className="h-4 w-4" />
                                <span className="font-medium">{element.element_name}</span>
                              </div>
                              <Badge 
                                variant={element.interactive ? "default" : "outline"} 
                                className="text-xs"
                              >
                                {element.interactive ? "Interactive" : "Static"}
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground mb-2">
                              {element.description}
                            </p>
                            <div className="flex items-center gap-2">
                              <Badge variant="outline" className="text-xs">
                                State: {element.state}
                              </Badge>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                      {environmentState.interactive_elements.length === 0 && (
                        <div className="col-span-2 text-center py-8">
                          <Settings className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                          <p className="text-muted-foreground">No interactive elements defined yet.</p>
                        </div>
                      )}
                    </div>
                  </TabsContent>
                )}

                {/* History Tab */}
                {state.showHistory && (
                  <TabsContent value="history" className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-medium">Environment Changes</h3>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onHistoryView?.(environmentState.id)}
                      >
                        <History className="h-4 w-4 mr-2" />
                        View Full History
                      </Button>
                    </div>
                    <ScrollArea className="h-48">
                      <div className="space-y-3">
                        {environmentState.environment_history.slice(0, 10).map((change, index) => (
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
                              <p className="text-sm text-muted-foreground mb-1">
                                {change.description}
                              </p>
                              {change.before_state && (
                                <div className="text-xs text-muted-foreground">
                                  <span className="line-through">{change.before_state}</span>
                                  <span className="mx-2">→</span>
                                  <span className="font-medium">{change.after_state}</span>
                                </div>
                              )}
                            </div>
                            <Badge variant={change.automatic ? "secondary" : "outline"} className="text-xs">
                              {change.automatic ? "Auto" : "Manual"}
                            </Badge>
                          </div>
                        ))}
                        {environmentState.environment_history.length === 0 && (
                          <div className="text-center py-8">
                            <History className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                            <p className="text-muted-foreground">No environment changes recorded yet.</p>
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

  if (environment_states.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <MapPin className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Environment States</h3>
          <p className="text-muted-foreground">
            Environment states will appear here once they are tracked for this scene.
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
          <MapPin className="h-6 w-6 text-primary" />
          <h2 className="text-xl font-semibold">Environment States</h2>
          <Badge variant="outline">{environment_states.length}</Badge>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setState(prev => ({ ...prev, showInteractiveElements: !prev.showInteractiveElements }))}
          >
            <Settings className="h-4 w-4 mr-2" />
            {state.showInteractiveElements ? 'Hide' : 'Show'} Elements
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setState(prev => ({ ...prev, showOccupants: !prev.showOccupants }))}
          >
            <Users className="h-4 w-4 mr-2" />
            {state.showOccupants ? 'Hide' : 'Show'} Occupants
          </Button>
        </div>
      </div>

      {/* Environment States */}
      <div className="space-y-4">
        {environment_states.map((environmentState) => (
          <div key={environmentState.id}>
            {renderEnvironmentState(environmentState)}
          </div>
        ))}
      </div>
    </div>
  )
} 