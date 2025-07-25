"use client"

import { useState, useEffect, useCallback, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import { Slider } from '@/components/ui/slider'
import { 
  FileText, 
  Edit3, 
  Save, 
  RefreshCw, 
  Download, 
  Share, 
  Eye, 
  EyeOff,
  Calendar,
  User,
  MessageSquare,
  TrendingUp,
  Clock,
  Copy,
  Undo,
  Redo,
  Settings,
  Loader2,
  AlertCircle,
  CheckCircle,
  X,
  Plus,
  Sparkles
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { format } from 'date-fns'
import type { 
  SceneSummary, 
  SummaryGenerationOptions, 
  SceneSummaryProps 
} from '@/types/scene'

interface EditingState {
  isEditing: boolean
  originalText: string
  currentText: string
  hasChanges: boolean
  history: string[]
  historyIndex: number
  wordCount: number
  characterCount: number
}

interface RegenerationOptions extends SummaryGenerationOptions {
  advanced: boolean
  customPrompt?: string
  includeAnalysis?: boolean
  preserveStructure?: boolean
}

const DEFAULT_REGENERATION_OPTIONS: RegenerationOptions = {
  focus: 'comprehensive',
  max_length: 500,
  include_details: true,
  formal_style: false,
  chronological: true,
  highlight_key_events: true,
  advanced: false
}

export function SceneSummaryDisplay({
  summary,
  onEdit,
  onRegenerate,
  onExport,
  editable = true,
  showMetadata = true,
  showRegenerateOptions = true
}: SceneSummaryProps) {
  const [editingState, setEditingState] = useState<EditingState>({
    isEditing: false,
    originalText: summary.summary_text,
    currentText: summary.summary_text,
    hasChanges: false,
    history: [summary.summary_text],
    historyIndex: 0,
    wordCount: summary.summary_text.split(/\s+/).length,
    characterCount: summary.summary_text.length
  })

  const [regenerationOptions, setRegenerationOptions] = useState<RegenerationOptions>(DEFAULT_REGENERATION_OPTIONS)
  const [showRegenerateDialog, setShowRegenerateDialog] = useState(false)
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'error' | null>(null)
  const [showMetadataPanel, setShowMetadataPanel] = useState(showMetadata)
  const [previewMode, setPreviewMode] = useState(false)

  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const autosaveTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Auto-save functionality
  useEffect(() => {
    if (editingState.hasChanges && editable) {
      if (autosaveTimeoutRef.current) {
        clearTimeout(autosaveTimeoutRef.current)
      }
      
      autosaveTimeoutRef.current = setTimeout(() => {
        handleSave(false) // Auto-save without closing edit mode
      }, 2000)
    }

    return () => {
      if (autosaveTimeoutRef.current) {
        clearTimeout(autosaveTimeoutRef.current)
      }
    }
  }, [editingState.hasChanges, editingState.currentText, editable])

  // Update word and character counts
  useEffect(() => {
    const words = editingState.currentText.trim().split(/\s+/).filter(word => word.length > 0)
    setEditingState(prev => ({
      ...prev,
      wordCount: words.length,
      characterCount: editingState.currentText.length
    }))
  }, [editingState.currentText])

  const handleEdit = useCallback(() => {
    setEditingState(prev => ({
      ...prev,
      isEditing: true,
      originalText: prev.currentText
    }))
  }, [])

  const handleTextChange = useCallback((text: string) => {
    setEditingState(prev => {
      const newHistory = prev.history.slice(0, prev.historyIndex + 1)
      newHistory.push(text)
      
      return {
        ...prev,
        currentText: text,
        hasChanges: text !== prev.originalText,
        history: newHistory,
        historyIndex: newHistory.length - 1
      }
    })
  }, [])

  const handleUndo = useCallback(() => {
    setEditingState(prev => {
      if (prev.historyIndex > 0) {
        const newIndex = prev.historyIndex - 1
        return {
          ...prev,
          currentText: prev.history[newIndex],
          historyIndex: newIndex,
          hasChanges: prev.history[newIndex] !== prev.originalText
        }
      }
      return prev
    })
  }, [])

  const handleRedo = useCallback(() => {
    setEditingState(prev => {
      if (prev.historyIndex < prev.history.length - 1) {
        const newIndex = prev.historyIndex + 1
        return {
          ...prev,
          currentText: prev.history[newIndex],
          historyIndex: newIndex,
          hasChanges: prev.history[newIndex] !== prev.originalText
        }
      }
      return prev
    })
  }, [])

  const handleSave = useCallback(async (closeEdit: boolean = true) => {
    if (!editingState.hasChanges || !onEdit) return

    setIsSaving(true)
    setSaveStatus('saving')

    try {
      await onEdit(summary.id, editingState.currentText)
      
      setEditingState(prev => ({
        ...prev,
        isEditing: !closeEdit,
        hasChanges: false,
        originalText: prev.currentText
      }))
      
      setSaveStatus('saved')
      setTimeout(() => setSaveStatus(null), 2000)
    } catch (error) {
      setSaveStatus('error')
      console.error('Failed to save summary:', error)
    } finally {
      setIsSaving(false)
    }
  }, [editingState.hasChanges, editingState.currentText, onEdit, summary.id])

  const handleCancel = useCallback(() => {
    setEditingState(prev => ({
      ...prev,
      isEditing: false,
      currentText: prev.originalText,
      hasChanges: false,
      history: [prev.originalText],
      historyIndex: 0
    }))
  }, [])

  const handleRegenerate = useCallback(async () => {
    if (!onRegenerate) return

    setIsRegenerating(true)
    setShowRegenerateDialog(false)

    try {
      await onRegenerate(summary.scene_id, regenerationOptions)
    } catch (error) {
      console.error('Failed to regenerate summary:', error)
    } finally {
      setIsRegenerating(false)
    }
  }, [onRegenerate, summary.scene_id, regenerationOptions])

  const handleExport = useCallback(async (format: 'txt' | 'json' | 'html') => {
    if (!onExport) return

    try {
      await onExport(summary)
      setShowExportDialog(false)
    } catch (error) {
      console.error('Failed to export summary:', error)
    }
  }, [onExport, summary])

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(editingState.currentText)
  }, [editingState.currentText])

  const handleShare = useCallback(() => {
    if (navigator.share) {
      navigator.share({
        title: `Scene Summary: ${summary.metadata.scene_name}`,
        text: editingState.currentText,
        url: window.location.href
      })
    } else {
      handleCopy()
    }
  }, [editingState.currentText, summary.metadata.scene_name])

  const formatTimestamp = (timestamp: string) => {
    return format(new Date(timestamp), 'MMM d, yyyy h:mm a')
  }

  const getSummaryTypeColor = (type: string) => {
    switch (type) {
      case 'comprehensive':
        return 'bg-blue-100 text-blue-800'
      case 'character':
        return 'bg-green-100 text-green-800'
      case 'plot':
        return 'bg-purple-100 text-purple-800'
      case 'environment':
        return 'bg-yellow-100 text-yellow-800'
      case 'catchup':
        return 'bg-orange-100 text-orange-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const canUndo = editingState.historyIndex > 0
  const canRedo = editingState.historyIndex < editingState.history.length - 1
  const isLongSummary = editingState.wordCount > 750

  return (
    <div className="space-y-6">
      {/* Summary Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Scene Summary
              <Badge variant="outline" className={getSummaryTypeColor(summary.summary_type)}>
                {summary.summary_type}
              </Badge>
            </CardTitle>
            <div className="flex items-center gap-2">
              {/* Save Status */}
              {saveStatus && (
                <div className="flex items-center gap-1 text-sm">
                  {saveStatus === 'saving' && <Loader2 className="h-4 w-4 animate-spin" />}
                  {saveStatus === 'saved' && <CheckCircle className="h-4 w-4 text-green-600" />}
                  {saveStatus === 'error' && <AlertCircle className="h-4 w-4 text-red-600" />}
                  <span className={cn(
                    saveStatus === 'saved' && 'text-green-600',
                    saveStatus === 'error' && 'text-red-600'
                  )}>
                    {saveStatus === 'saving' && 'Saving...'}
                    {saveStatus === 'saved' && 'Saved'}
                    {saveStatus === 'error' && 'Error saving'}
                  </span>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowMetadataPanel(!showMetadataPanel)}
                >
                  <Settings className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setPreviewMode(!previewMode)}
                >
                  {previewMode ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCopy}
                >
                  <Copy className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleShare}
                >
                  <Share className="h-4 w-4" />
                </Button>
                {showRegenerateOptions && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowRegenerateDialog(true)}
                    disabled={isRegenerating}
                  >
                    {isRegenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowExportDialog(true)}
                >
                  <Download className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Main Summary Content */}
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">
                  {summary.metadata.scene_name}
                </CardTitle>
                {editable && (
                  <div className="flex items-center gap-2">
                    {editingState.isEditing ? (
                      <>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleUndo}
                          disabled={!canUndo}
                        >
                          <Undo className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleRedo}
                          disabled={!canRedo}
                        >
                          <Redo className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleCancel}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() => handleSave(true)}
                          disabled={!editingState.hasChanges || isSaving}
                        >
                          {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                        </Button>
                      </>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleEdit}
                      >
                        <Edit3 className="h-4 w-4 mr-2" />
                        Edit
                      </Button>
                    )}
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {editingState.isEditing ? (
                <div className="space-y-4">
                  <Textarea
                    ref={textareaRef}
                    value={editingState.currentText}
                    onChange={(e) => handleTextChange(e.target.value)}
                    className="min-h-[400px] resize-vertical"
                    placeholder="Enter your scene summary..."
                  />
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <div className="flex items-center gap-4">
                      <span>{editingState.wordCount} words</span>
                      <span>{editingState.characterCount} characters</span>
                      {editingState.hasChanges && (
                        <Badge variant="outline" className="text-xs">
                          Unsaved changes
                        </Badge>
                      )}
                    </div>
                    {isLongSummary && (
                      <Badge variant="outline" className="text-xs text-orange-600">
                        Long summary
                      </Badge>
                    )}
                  </div>
                </div>
              ) : (
                <div className={cn(
                  "prose prose-sm max-w-none",
                  previewMode && "prose-lg"
                )}>
                  {editingState.currentText.split('\n').map((paragraph, index) => (
                    <p key={index} className="mb-4 last:mb-0">
                      {paragraph}
                    </p>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Metadata Panel */}
        {showMetadataPanel && (
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Summary Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Type</Label>
                  <Badge variant="outline" className={getSummaryTypeColor(summary.summary_type)}>
                    {summary.summary_type}
                  </Badge>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium">Generated</Label>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    {formatTimestamp(summary.generated_at)}
                  </div>
                </div>

                {summary.edited_at && (
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Last Edited</Label>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Edit3 className="h-4 w-4" />
                      {formatTimestamp(summary.edited_at)}
                    </div>
                  </div>
                )}

                <Separator />

                <div className="space-y-2">
                  <Label className="text-sm font-medium">Statistics</Label>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-muted-foreground">Poses:</span>
                      <span className="ml-2">{summary.metadata.pose_count}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Characters:</span>
                      <span className="ml-2">{summary.metadata.character_count}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Words:</span>
                      <span className="ml-2">{editingState.wordCount}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Length:</span>
                      <span className="ml-2">{editingState.characterCount}</span>
                    </div>
                  </div>
                </div>

                {summary.metadata.character_focus && (
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Character Focus</Label>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <User className="h-4 w-4" />
                      {summary.metadata.character_focus}
                    </div>
                  </div>
                )}

                {summary.metadata.key_events && summary.metadata.key_events.length > 0 && (
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Key Events</Label>
                    <div className="space-y-1">
                      {summary.metadata.key_events.map((event, index) => (
                        <div key={index} className="flex items-center gap-2 text-sm text-muted-foreground">
                          <TrendingUp className="h-3 w-3" />
                          {event}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <Separator />

                <div className="space-y-2">
                  <Label className="text-sm font-medium">Status</Label>
                  <div className="flex items-center gap-2">
                    <Badge variant={summary.is_editable ? 'default' : 'secondary'}>
                      {summary.is_editable ? 'Editable' : 'Read-only'}
                    </Badge>
                    {editingState.hasChanges && (
                      <Badge variant="outline" className="text-xs">
                        Modified
                      </Badge>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Regeneration Dialog */}
      <Dialog open={showRegenerateDialog} onOpenChange={setShowRegenerateDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              Regenerate Summary
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Focus</Label>
              <Select
                value={regenerationOptions.focus}
                onValueChange={(value: any) => setRegenerationOptions(prev => ({ ...prev, focus: value }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="comprehensive">Comprehensive</SelectItem>
                  <SelectItem value="character">Character-focused</SelectItem>
                  <SelectItem value="plot">Plot-focused</SelectItem>
                  <SelectItem value="environment">Environment-focused</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Max Length: {regenerationOptions.max_length} words</Label>
              <Slider
                value={[regenerationOptions.max_length]}
                onValueChange={(value) => setRegenerationOptions(prev => ({ ...prev, max_length: value[0] }))}
                max={1000}
                min={100}
                step={50}
              />
            </div>

            <div className="space-y-2">
              <Label>Options</Label>
              <div className="space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <Checkbox
                    checked={regenerationOptions.include_details}
                    onCheckedChange={(checked) => setRegenerationOptions(prev => ({ ...prev, include_details: Boolean(checked) }))}
                  />
                  <span className="text-sm">Include details</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <Checkbox
                    checked={regenerationOptions.formal_style}
                    onCheckedChange={(checked) => setRegenerationOptions(prev => ({ ...prev, formal_style: Boolean(checked) }))}
                  />
                  <span className="text-sm">Formal style</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <Checkbox
                    checked={regenerationOptions.chronological}
                    onCheckedChange={(checked) => setRegenerationOptions(prev => ({ ...prev, chronological: Boolean(checked) }))}
                  />
                  <span className="text-sm">Chronological order</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <Checkbox
                    checked={regenerationOptions.highlight_key_events}
                    onCheckedChange={(checked) => setRegenerationOptions(prev => ({ ...prev, highlight_key_events: Boolean(checked) }))}
                  />
                  <span className="text-sm">Highlight key events</span>
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowRegenerateDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleRegenerate} disabled={isRegenerating}>
                {isRegenerating ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Sparkles className="h-4 w-4 mr-2" />}
                Regenerate
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Export Dialog */}
      <Dialog open={showExportDialog} onOpenChange={setShowExportDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Download className="h-5 w-5" />
              Export Summary
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-2">
              <Button
                variant="outline"
                onClick={() => handleExport('txt')}
                className="flex flex-col items-center gap-2 h-auto py-4"
              >
                <FileText className="h-6 w-6" />
                <span className="text-sm">TXT</span>
              </Button>
              <Button
                variant="outline"
                onClick={() => handleExport('json')}
                className="flex flex-col items-center gap-2 h-auto py-4"
              >
                <FileText className="h-6 w-6" />
                <span className="text-sm">JSON</span>
              </Button>
              <Button
                variant="outline"
                onClick={() => handleExport('html')}
                className="flex flex-col items-center gap-2 h-auto py-4"
              >
                <FileText className="h-6 w-6" />
                <span className="text-sm">HTML</span>
              </Button>
            </div>
            <p className="text-sm text-muted-foreground text-center">
              Choose a format to export your summary
            </p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
} 