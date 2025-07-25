"use client"

import { useState, useEffect, useCallback, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import { 
  Sparkles, 
  Settings, 
  Download, 
  Save, 
  Copy, 
  RefreshCw, 
  Edit, 
  Eye, 
  EyeOff,
  ChevronDown,
  ChevronUp,
  FileText,
  Users,
  MapPin,
  BookOpen,
  Clock,
  Target,
  Layers,
  Wand2,
  History,
  Share,
  Template,
  Palette,
  Filter,
  BarChart,
  PieChart,
  Calendar,
  Tag,
  Loader2,
  CheckCircle,
  AlertCircle,
  Info,
  Star,
  TrendingUp
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { useToast } from '@/hooks/use-toast'
import { format } from 'date-fns'

interface SummaryTemplate {
  id: string
  name: string
  description: string
  focus: 'comprehensive' | 'character' | 'plot' | 'environment'
  style: 'narrative' | 'analytical' | 'bullet_points' | 'timeline'
  template: string
  default_options: SummaryGenerationOptions
}

interface SummaryGenerationOptions {
  focus: 'comprehensive' | 'character' | 'plot' | 'environment'
  character_id?: string
  max_length: number
  include_details: boolean
  formal_style: boolean
  chronological: boolean
  highlight_key_events: boolean
  include_dialogue: boolean
  include_emotions: boolean
  include_relationships: boolean
  include_setting: boolean
  writing_style: 'narrative' | 'analytical' | 'bullet_points' | 'timeline'
  perspective: 'third_person' | 'omniscient' | 'character_focused'
  detail_level: 'brief' | 'standard' | 'detailed' | 'comprehensive'
  include_statistics: boolean
  custom_instructions?: string
}

interface GeneratedSummary {
  id: string
  scene_id: string
  summary_text: string
  summary_type: string
  generated_at: string
  generation_time: number
  word_count: number
  options: SummaryGenerationOptions
  template_used?: string
  metadata: {
    scene_name: string
    character_count: number
    pose_count: number
    date_range: { start: string; end: string }
    key_characters: string[]
    key_events: string[]
    themes: string[]
    emotions: string[]
    locations: string[]
  }
}

interface SummaryStats {
  total_words: number
  reading_time: number
  key_events_count: number
  characters_mentioned: number
  dialogue_percentage: number
  emotion_score: number
  complexity_score: number
}

const DEFAULT_OPTIONS: SummaryGenerationOptions = {
  focus: 'comprehensive',
  max_length: 500,
  include_details: true,
  formal_style: false,
  chronological: true,
  highlight_key_events: true,
  include_dialogue: false,
  include_emotions: true,
  include_relationships: true,
  include_setting: true,
  writing_style: 'narrative',
  perspective: 'third_person',
  detail_level: 'standard',
  include_statistics: false
}

const SUMMARY_TEMPLATES: SummaryTemplate[] = [
  {
    id: 'comprehensive',
    name: 'Comprehensive Overview',
    description: 'Detailed summary covering all aspects of the scene',
    focus: 'comprehensive',
    style: 'narrative',
    template: 'A comprehensive overview that covers characters, plot, environment, and key events in narrative form.',
    default_options: { ...DEFAULT_OPTIONS, focus: 'comprehensive', max_length: 750 }
  },
  {
    id: 'character_focused',
    name: 'Character-Focused',
    description: 'Summary centered on character development and interactions',
    focus: 'character',
    style: 'narrative',
    template: 'A character-focused summary highlighting personal growth, relationships, and emotional journey.',
    default_options: { 
      ...DEFAULT_OPTIONS, 
      focus: 'character', 
      max_length: 400, 
      include_emotions: true, 
      include_relationships: true 
    }
  },
  {
    id: 'plot_progression',
    name: 'Plot Progression',
    description: 'Summary focused on story advancement and key events',
    focus: 'plot',
    style: 'analytical',
    template: 'A plot-focused summary analyzing story progression, conflicts, and resolutions.',
    default_options: { 
      ...DEFAULT_OPTIONS, 
      focus: 'plot', 
      max_length: 450, 
      highlight_key_events: true,
      writing_style: 'analytical'
    }
  },
  {
    id: 'quick_recap',
    name: 'Quick Recap',
    description: 'Brief bullet-point summary of key events',
    focus: 'comprehensive',
    style: 'bullet_points',
    template: 'A concise bullet-point recap of the most important events and outcomes.',
    default_options: { 
      ...DEFAULT_OPTIONS, 
      max_length: 200, 
      writing_style: 'bullet_points',
      detail_level: 'brief'
    }
  },
  {
    id: 'timeline',
    name: 'Timeline Summary',
    description: 'Chronological timeline of events',
    focus: 'comprehensive',
    style: 'timeline',
    template: 'A chronological timeline highlighting when key events occurred.',
    default_options: { 
      ...DEFAULT_OPTIONS, 
      writing_style: 'timeline',
      chronological: true,
      include_statistics: true
    }
  }
]

export interface AdvancedSummaryInterfaceProps {
  sceneId: string
  sceneName?: string
  onSummaryGenerated?: (summary: GeneratedSummary) => void
  onSummaryEdited?: (summaryId: string, newText: string) => void
  onSummaryExported?: (summary: GeneratedSummary, format: string) => void
  availableCharacters?: Array<{ id: string; name: string }>
  existingSummaries?: GeneratedSummary[]
  allowCustomTemplates?: boolean
  enableAnalytics?: boolean
  className?: string
}

export function AdvancedSummaryInterface({
  sceneId,
  sceneName,
  onSummaryGenerated,
  onSummaryEdited,
  onSummaryExported,
  availableCharacters = [],
  existingSummaries = [],
  allowCustomTemplates = true,
  enableAnalytics = true,
  className
}: AdvancedSummaryInterfaceProps) {
  const [options, setOptions] = useState<SummaryGenerationOptions>(DEFAULT_OPTIONS)
  const [selectedTemplate, setSelectedTemplate] = useState<string>('comprehensive')
  const [customTemplate, setCustomTemplate] = useState<string>('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedSummary, setGeneratedSummary] = useState<GeneratedSummary | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editedText, setEditedText] = useState('')
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false)
  const [showTemplateDialog, setShowTemplateDialog] = useState(false)
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [generationProgress, setGenerationProgress] = useState(0)
  const [summaryStats, setSummaryStats] = useState<SummaryStats | null>(null)
  const [previewMode, setPreviewMode] = useState(false)

  const { toast } = useToast()

  // Apply template settings when template changes
  useEffect(() => {
    const template = SUMMARY_TEMPLATES.find(t => t.id === selectedTemplate)
    if (template) {
      setOptions(template.default_options)
    }
  }, [selectedTemplate])

  // Calculate summary statistics
  const calculateSummaryStats = useCallback((summary: GeneratedSummary): SummaryStats => {
    const text = summary.summary_text
    const words = text.split(/\s+/).length
    const readingTime = Math.ceil(words / 200) // Average reading speed
    
    // Simple heuristics for analysis
    const keyEventMatches = (text.match(/\b(suddenly|then|after|before|when|during)\b/gi) || []).length
    const characterMatches = summary.metadata.key_characters.length
    const dialogueMatches = (text.match(/[""][^""]*[""]|'[^']*'/g) || []).length
    const dialoguePercentage = (dialogueMatches * 20) / words * 100 // Rough estimate
    
    const emotionWords = ['happy', 'sad', 'angry', 'excited', 'nervous', 'calm', 'frustrated', 'joy', 'fear', 'love']
    const emotionScore = emotionWords.reduce((score, word) => {
      const matches = (text.toLowerCase().match(new RegExp(`\\b${word}\\b`, 'g')) || []).length
      return score + matches
    }, 0) / words * 100

    return {
      total_words: words,
      reading_time: readingTime,
      key_events_count: keyEventMatches,
      characters_mentioned: characterMatches,
      dialogue_percentage: Math.min(dialoguePercentage, 100),
      emotion_score: Math.min(emotionScore * 10, 100),
      complexity_score: Math.min((keyEventMatches + characterMatches) * 5, 100)
    }
  }, [])

  const handleOptionChange = (key: keyof SummaryGenerationOptions, value: any) => {
    setOptions(prev => ({ ...prev, [key]: value }))
  }

  const generateSummary = useCallback(async () => {
    setIsGenerating(true)
    setGenerationProgress(0)

    // Simulate progress updates
    const progressInterval = setInterval(() => {
      setGenerationProgress(prev => Math.min(prev + 10, 90))
    }, 200)

    try {
      const requestBody = {
        ...options,
        template: selectedTemplate !== 'custom' ? selectedTemplate : undefined,
        custom_template: selectedTemplate === 'custom' ? customTemplate : undefined
      }

      const response = await fetch(`/api/search-summary/summaries/scenes/${sceneId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) {
        throw new Error('Failed to generate summary')
      }

      const data = await response.json()
      
      if (data.success) {
        const summary = data.data as GeneratedSummary
        setGeneratedSummary(summary)
        setEditedText(summary.summary_text)
        
        // Calculate statistics
        const stats = calculateSummaryStats(summary)
        setSummaryStats(stats)

        if (onSummaryGenerated) {
          onSummaryGenerated(summary)
        }

        toast({
          title: "Summary Generated",
          description: `Generated ${summary.word_count} word summary in ${summary.generation_time}ms.`
        })
      } else {
        throw new Error(data.message || 'Summary generation failed')
      }
    } catch (error) {
      toast({
        title: "Generation Failed",
        description: error instanceof Error ? error.message : 'Failed to generate summary',
        variant: "destructive"
      })
    } finally {
      clearInterval(progressInterval)
      setGenerationProgress(100)
      setIsGenerating(false)
    }
  }, [sceneId, options, selectedTemplate, customTemplate, onSummaryGenerated, calculateSummaryStats, toast])

  const handleSaveEdit = useCallback(async () => {
    if (!generatedSummary || !onSummaryEdited) return

    try {
      await onSummaryEdited(generatedSummary.id, editedText)
      setGeneratedSummary(prev => prev ? { ...prev, summary_text: editedText } : null)
      setIsEditing(false)
      
      toast({
        title: "Summary Updated",
        description: "Your changes have been saved successfully."
      })
    } catch (error) {
      toast({
        title: "Save Failed",
        description: "Failed to save your changes. Please try again.",
        variant: "destructive"
      })
    }
  }, [generatedSummary, editedText, onSummaryEdited, toast])

  const handleExport = useCallback(async (format: string) => {
    if (!generatedSummary || !onSummaryExported) return

    try {
      await onSummaryExported(generatedSummary, format)
      setShowExportDialog(false)
      
      toast({
        title: "Export Successful",
        description: `Summary exported in ${format.toUpperCase()} format.`
      })
    } catch (error) {
      toast({
        title: "Export Failed", 
        description: "Failed to export summary. Please try again.",
        variant: "destructive"
      })
    }
  }, [generatedSummary, onSummaryExported, toast])

  const wordCountColor = useMemo(() => {
    if (!generatedSummary) return 'text-muted-foreground'
    const ratio = generatedSummary.word_count / options.max_length
    if (ratio < 0.5) return 'text-blue-500'
    if (ratio < 0.8) return 'text-green-500'
    if (ratio < 1) return 'text-yellow-500'
    return 'text-red-500'
  }, [generatedSummary, options.max_length])

  return (
    <div className={cn("space-y-6", className)}>
      {/* Summary Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Summary Generation
            {sceneName && (
              <Badge variant="secondary">{sceneName}</Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Template Selection */}
          <div className="space-y-3">
            <Label>Summary Template</Label>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {SUMMARY_TEMPLATES.map(template => (
                <Card 
                  key={template.id}
                  className={cn(
                    "cursor-pointer transition-all hover:shadow-md",
                    selectedTemplate === template.id && "ring-2 ring-primary"
                  )}
                  onClick={() => setSelectedTemplate(template.id)}
                >
                  <CardContent className="p-4">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Template className="h-4 w-4" />
                        <span className="font-medium">{template.name}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {template.description}
                      </p>
                      <div className="flex items-center gap-1">
                        <Badge variant="outline" className="text-xs">
                          {template.focus}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {template.default_options.max_length} words
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
              
              {allowCustomTemplates && (
                <Card 
                  className={cn(
                    "cursor-pointer transition-all hover:shadow-md border-dashed",
                    selectedTemplate === 'custom' && "ring-2 ring-primary"
                  )}
                  onClick={() => setShowTemplateDialog(true)}
                >
                  <CardContent className="p-4">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Wand2 className="h-4 w-4" />
                        <span className="font-medium">Custom Template</span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Create your own summary template with custom instructions.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>

          {/* Quick Configuration */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label>Focus</Label>
              <Select 
                value={options.focus} 
                onValueChange={(value: any) => handleOptionChange('focus', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="comprehensive">
                    <div className="flex items-center gap-2">
                      <Layers className="h-4 w-4" />
                      Comprehensive
                    </div>
                  </SelectItem>
                  <SelectItem value="character">
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4" />
                      Character
                    </div>
                  </SelectItem>
                  <SelectItem value="plot">
                    <div className="flex items-center gap-2">
                      <BookOpen className="h-4 w-4" />
                      Plot
                    </div>
                  </SelectItem>
                  <SelectItem value="environment">
                    <div className="flex items-center gap-2">
                      <MapPin className="h-4 w-4" />
                      Environment
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {options.focus === 'character' && (
              <div className="space-y-2">
                <Label>Character</Label>
                <Select 
                  value={options.character_id || ''} 
                  onValueChange={(value) => handleOptionChange('character_id', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select character" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableCharacters.map(character => (
                      <SelectItem key={character.id} value={character.id}>
                        {character.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="space-y-2">
              <Label>Length: {options.max_length} words</Label>
              <Slider
                value={[options.max_length]}
                onValueChange={(value) => handleOptionChange('max_length', value[0])}
                max={1000}
                min={100}
                step={50}
              />
            </div>

            <div className="space-y-2">
              <Label>Style</Label>
              <Select 
                value={options.writing_style} 
                onValueChange={(value: any) => handleOptionChange('writing_style', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="narrative">Narrative</SelectItem>
                  <SelectItem value="analytical">Analytical</SelectItem>
                  <SelectItem value="bullet_points">Bullet Points</SelectItem>
                  <SelectItem value="timeline">Timeline</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Advanced Options Toggle */}
          <Collapsible open={showAdvancedOptions} onOpenChange={setShowAdvancedOptions}>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" className="w-full justify-between">
                Advanced Options
                {showAdvancedOptions ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-4 pt-4 border-t">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="flex items-center space-x-2">
                  <Switch
                    id="include-details"
                    checked={options.include_details}
                    onCheckedChange={(checked) => handleOptionChange('include_details', checked)}
                  />
                  <Label htmlFor="include-details">Include Details</Label>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Switch
                    id="chronological"
                    checked={options.chronological}
                    onCheckedChange={(checked) => handleOptionChange('chronological', checked)}
                  />
                  <Label htmlFor="chronological">Chronological</Label>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Switch
                    id="highlight-events"
                    checked={options.highlight_key_events}
                    onCheckedChange={(checked) => handleOptionChange('highlight_key_events', checked)}
                  />
                  <Label htmlFor="highlight-events">Highlight Key Events</Label>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Switch
                    id="include-dialogue"
                    checked={options.include_dialogue}
                    onCheckedChange={(checked) => handleOptionChange('include_dialogue', checked)}
                  />
                  <Label htmlFor="include-dialogue">Include Dialogue</Label>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Switch
                    id="include-emotions"
                    checked={options.include_emotions}
                    onCheckedChange={(checked) => handleOptionChange('include_emotions', checked)}
                  />
                  <Label htmlFor="include-emotions">Include Emotions</Label>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Switch
                    id="include-relationships"
                    checked={options.include_relationships}
                    onCheckedChange={(checked) => handleOptionChange('include_relationships', checked)}
                  />
                  <Label htmlFor="include-relationships">Include Relationships</Label>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Custom Instructions (Optional)</Label>
                <Textarea
                  placeholder="Add any specific instructions for the summary generation..."
                  value={options.custom_instructions || ''}
                  onChange={(e) => handleOptionChange('custom_instructions', e.target.value)}
                  rows={3}
                />
              </div>
            </CollapsibleContent>
          </Collapsible>

          {/* Generation Button */}
          <div className="flex gap-2">
            <Button 
              onClick={generateSummary} 
              disabled={isGenerating}
              className="flex-1"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Generate Summary
                </>
              )}
            </Button>
            
            {existingSummaries.length > 0 && (
              <Button variant="outline">
                <History className="h-4 w-4 mr-2" />
                History ({existingSummaries.length})
              </Button>
            )}
          </div>

          {/* Generation Progress */}
          {isGenerating && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Generating summary...</span>
                <span>{generationProgress}%</span>
              </div>
              <Progress value={generationProgress} />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Generated Summary Display */}
      {generatedSummary && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Generated Summary
                <Badge variant="secondary" className={wordCountColor}>
                  {generatedSummary.word_count} words
                </Badge>
              </CardTitle>
              
              <div className="flex items-center gap-2">
                {!isEditing && (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPreviewMode(!previewMode)}
                    >
                      {previewMode ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setIsEditing(true)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowExportDialog(true)}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </>
                )}
                
                {isEditing && (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setIsEditing(false)
                        setEditedText(generatedSummary.summary_text)
                      }}
                    >
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      onClick={handleSaveEdit}
                    >
                      <Save className="h-4 w-4 mr-2" />
                      Save
                    </Button>
                  </>
                )}
              </div>
            </div>
          </CardHeader>
          
          <CardContent className="space-y-4">
            {/* Summary Content */}
            {isEditing ? (
              <Textarea
                value={editedText}
                onChange={(e) => setEditedText(e.target.value)}
                className="min-h-[300px] resize-vertical"
              />
            ) : (
              <div 
                className={cn(
                  "prose prose-sm max-w-none",
                  previewMode && "bg-muted/50 p-4 rounded-lg"
                )}
              >
                {generatedSummary.summary_text}
              </div>
            )}

            {/* Summary Statistics */}
            {summaryStats && enableAnalytics && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-500">
                    {summaryStats.reading_time}
                  </div>
                  <div className="text-xs text-muted-foreground">min read</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-500">
                    {summaryStats.key_events_count}
                  </div>
                  <div className="text-xs text-muted-foreground">key events</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-500">
                    {summaryStats.characters_mentioned}
                  </div>
                  <div className="text-xs text-muted-foreground">characters</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-500">
                    {Math.round(summaryStats.emotion_score)}%
                  </div>
                  <div className="text-xs text-muted-foreground">emotion</div>
                </div>
              </div>
            )}

            {/* Metadata */}
            <Collapsible>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm" className="w-full justify-between">
                  <span className="flex items-center gap-2">
                    <Info className="h-4 w-4" />
                    Summary Details
                  </span>
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="pt-2">
                <div className="text-xs text-muted-foreground space-y-1">
                  <div>Generated: {format(new Date(generatedSummary.generated_at), 'PPp')}</div>
                  <div>Generation time: {generatedSummary.generation_time}ms</div>
                  <div>Template: {selectedTemplate}</div>
                  {generatedSummary.metadata.key_characters.length > 0 && (
                    <div>Characters: {generatedSummary.metadata.key_characters.join(', ')}</div>
                  )}
                  {generatedSummary.metadata.themes.length > 0 && (
                    <div>Themes: {generatedSummary.metadata.themes.join(', ')}</div>
                  )}
                </div>
              </CollapsibleContent>
            </Collapsible>
          </CardContent>
        </Card>
      )}

      {/* Custom Template Dialog */}
      <Dialog open={showTemplateDialog} onOpenChange={setShowTemplateDialog}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Custom Summary Template</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Custom Instructions</Label>
              <Textarea
                placeholder="Enter your custom summary instructions here..."
                value={customTemplate}
                onChange={(e) => setCustomTemplate(e.target.value)}
                rows={6}
              />
            </div>
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                Provide specific instructions for how you want the summary to be structured and what elements to focus on.
              </AlertDescription>
            </Alert>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTemplateDialog(false)}>
              Cancel
            </Button>
            <Button onClick={() => {
              setSelectedTemplate('custom')
              setShowTemplateDialog(false)
            }}>
              Use Custom Template
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Export Dialog */}
      <Dialog open={showExportDialog} onOpenChange={setShowExportDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Export Summary</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Export your summary in your preferred format.
            </p>
            <div className="grid grid-cols-3 gap-2">
              <Button 
                onClick={() => handleExport('json')} 
                className="flex-col gap-1 h-16"
              >
                <FileText className="h-6 w-6" />
                JSON
              </Button>
              <Button 
                onClick={() => handleExport('txt')} 
                className="flex-col gap-1 h-16"
              >
                <FileText className="h-6 w-6" />
                Text
              </Button>
              <Button 
                onClick={() => handleExport('pdf')} 
                className="flex-col gap-1 h-16"
              >
                <FileText className="h-6 w-6" />
                PDF
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
} 