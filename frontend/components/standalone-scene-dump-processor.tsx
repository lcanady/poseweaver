"use client"

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import { Label } from '@/components/ui/label'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Textarea } from '@/components/ui/textarea'
import { 
  Zap, 
  Upload, 
  CheckCircle, 
  XCircle, 
  Loader2, 
  Settings, 
  Users, 
  MessageSquare,
  Clock,
  AlertCircle,
  RefreshCw,
  Sparkles,
  Eye,
  EyeOff
} from 'lucide-react'
import { cn } from '../lib/utils'
import { VeniceClient, type ProcessedPose, type VeniceProcessingResult } from '../lib/venice-client'

interface StandaloneSceneDumpProcessorProps {
  // Required props
  veniceApiKey: string
  userId: string
  userDisplayName: string
  sceneId?: string
  sceneTitle?: string
  className?: string
  
  // Optional configuration
  autoProcess?: boolean
  onProcessingComplete?: (result: VeniceProcessingResult & { sceneId?: string }) => void
  onSaveToScene?: (poses: ProcessedPose[], sceneId: string) => Promise<boolean>
}

export function StandaloneSceneDumpProcessor({
  veniceApiKey,
  userId,
  userDisplayName,
  sceneId,
  sceneTitle,
  className,
  autoProcess = false,
  onProcessingComplete,
  onSaveToScene
}: StandaloneSceneDumpProcessorProps) {
  const [sceneDumpText, setSceneDumpText] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [lastResult, setLastResult] = useState<VeniceProcessingResult & { sceneId?: string } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  const [settings, setSettings] = useState({
    autoProcess: autoProcess,
    processingFormat: 'mush_output' as 'simple' | 'character_prefix' | 'mush_output',
    includeEnhancement: false,
    enhancementStyle: 'balanced' as 'balanced' | 'dramatic' | 'subtle',
  })

  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false)
  const [showPoseDetails, setShowPoseDetails] = useState(false)

  // Initialize Venice client
  const veniceClient = new VeniceClient(veniceApiKey)

  // Auto-process when enabled and scene dump text changes
  useEffect(() => {
    if (settings.autoProcess && sceneDumpText?.trim() && !isProcessing) {
      handleProcess()
    }
  }, [sceneDumpText, settings.autoProcess])

  const handleProcess = async () => {
    if (!sceneDumpText?.trim()) {
      setError('Scene dump text is required')
      return
    }

    if (!veniceApiKey) {
      setError('Venice API key is required for processing')
      return
    }

    setIsProcessing(true)
    setError(null)

    try {
      // Extract character name from user display name or scene dump
      const characterName = extractCharacterName(sceneDumpText, userDisplayName)
      
      // Process the scene dump using Venice client
      const result = await veniceClient.processSceneDump(
        sceneDumpText,
        characterName,
        {
          apiKey: veniceApiKey,
          enhancementStyle: settings.includeEnhancement ? settings.enhancementStyle : undefined
        }
      )

      const finalResult = {
        ...result,
        sceneId: sceneId
      }

      setLastResult(finalResult)
      
      if (result.success) {
        // Try to save to scene if callback provided
        if (onSaveToScene && sceneId && result.poses.length > 0) {
          setIsSaving(true)
          try {
            const saveSuccess = await onSaveToScene(result.poses, sceneId)
            if (!saveSuccess) {
              console.warn('Failed to save poses to scene, but processing succeeded')
            }
          } catch (saveError) {
            console.warn('Error saving to scene:', saveError)
          } finally {
            setIsSaving(false)
          }
        }
        
        if (onProcessingComplete) {
          onProcessingComplete(finalResult)
        }
      } else {
        setError(result.error || 'Processing failed')
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      setError(errorMessage)
      setLastResult({
        success: false,
        poses: [],
        error: errorMessage,
        sceneId: sceneId
      })
    } finally {
      setIsProcessing(false)
    }
  }

  const extractCharacterName = (text: string, fallback: string): string => {
    const lines = text.split('\n').map(line => line.trim()).filter(Boolean)
    
    for (const line of lines) {
      const nameMatch = line.match(/^([A-Z][a-zA-Z]+)(?:\s+(?:says|asks|tells|whispers|shouts|nods|looks|moves|walks|goes)|:)/)
      if (nameMatch) {
        return nameMatch[1]
      }
    }
    
    return fallback?.split(' ')[0] || 'Player'
  }

  const clearError = () => {
    setError(null)
  }

  const getProcessingStatusBadge = () => {
    if (isProcessing || isSaving) {
      return <Badge variant="secondary" className="gap-1">
        <Loader2 className="h-3 w-3 animate-spin" />
        {isProcessing ? 'Processing...' : 'Saving...'}
      </Badge>
    }

    if (error) {
      return <Badge variant="destructive" className="gap-1">
        <XCircle className="h-3 w-3" />
        Failed
      </Badge>
    }

    if (lastResult?.success) {
      return <Badge variant="default" className="gap-1 bg-green-600">
        <CheckCircle className="h-3 w-3" />
        Success
      </Badge>
    }

    return <Badge variant="outline" className="gap-1">
      <Clock className="h-3 w-3" />
      Ready
    </Badge>
  }

  const formatPoseType = (type: string) => {
    const typeMap = {
      'action': 'Action',
      'dialogue': 'Dialogue', 
      'narrative': 'Narrative',
      'internal': 'Internal',
      'mixed': 'Mixed'
    }
    return typeMap[type as keyof typeof typeMap] || type
  }

  const getCharacterStats = () => {
    if (!lastResult?.poses) return {}
    
    const stats: Record<string, number> = {}
    lastResult.poses.forEach(pose => {
      stats[pose.character_name] = (stats[pose.character_name] || 0) + 1
    })
    
    return stats
  }

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Zap className="h-5 w-5" />
              Standalone Scene Dump Processor
            </CardTitle>
            <CardDescription>
              Process scene dump content directly with Venice.ai
            </CardDescription>
          </div>
          {getProcessingStatusBadge()}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Error Display */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <div className="flex flex-col gap-2">
                <div className="font-medium">Processing Error:</div>
                <div className="text-sm">{error}</div>
                <Button variant="ghost" size="sm" onClick={clearError} className="w-fit">
                  <XCircle className="h-4 w-4" />
                  Dismiss
                </Button>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Scene Dump Input */}
        <div className="space-y-2">
          <Label htmlFor="scene-dump">Scene Dump Text</Label>
          <Textarea
            id="scene-dump"
            placeholder="Paste your MUSH scene dump here..."
            value={sceneDumpText}
            onChange={(e) => setSceneDumpText(e.target.value)}
            rows={8}
            className="font-mono text-sm"
          />
        </div>

        {/* Quick Actions */}
        <div className="flex flex-wrap items-center gap-3">
          <Button 
            onClick={handleProcess}
            disabled={isProcessing || isSaving || !sceneDumpText?.trim()}
            className="gap-2"
          >
            {isProcessing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Upload className="h-4 w-4" />
            )}
            Process Dump
          </Button>

          <div className="flex items-center gap-2">
            <Switch
              id="auto-process"
              checked={settings.autoProcess}
              onCheckedChange={(checked) => 
                setSettings(prev => ({ ...prev, autoProcess: checked }))
              }
            />
            <Label htmlFor="auto-process" className="text-sm">Auto-process</Label>
          </div>

          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
            className="gap-1"
          >
            <Settings className="h-4 w-4" />
            Settings
          </Button>
        </div>

        {/* Advanced Options */}
        {showAdvancedOptions && (
          <>
            <Separator />
            <div className="space-y-3">
              <h4 className="text-sm font-medium">Processing Options</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label className="text-xs">Format</Label>
                  <Select 
                    value={settings.processingFormat} 
                    onValueChange={(value: any) => 
                      setSettings(prev => ({ ...prev, processingFormat: value }))
                    }
                  >
                    <SelectTrigger className="h-8">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="mush_output">MUSH Output</SelectItem>
                      <SelectItem value="character_prefix">Character Prefix</SelectItem>
                      <SelectItem value="simple">Simple</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Switch
                      id="enhancement"
                      checked={settings.includeEnhancement}
                      onCheckedChange={(checked) => 
                        setSettings(prev => ({ ...prev, includeEnhancement: checked }))
                      }
                    />
                    <Label htmlFor="enhancement" className="text-xs flex items-center gap-1">
                      <Sparkles className="h-3 w-3" />
                      Enhancement
                    </Label>
                  </div>
                  
                  {settings.includeEnhancement && (
                    <Select 
                      value={settings.enhancementStyle} 
                      onValueChange={(value: any) => 
                        setSettings(prev => ({ ...prev, enhancementStyle: value }))
                      }
                    >
                      <SelectTrigger className="h-8">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="balanced">Balanced</SelectItem>
                        <SelectItem value="dramatic">Dramatic</SelectItem>
                        <SelectItem value="subtle">Subtle</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                  

                </div>
              </div>
            </div>
          </>
        )}

        {/* Scene Info */}
        {sceneId && sceneTitle && (
          <>
            <Separator />
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <MessageSquare className="h-4 w-4" />
              Scene: <span className="font-medium">{sceneTitle}</span>
            </div>
          </>
        )}

        {/* Processing Results */}
        {lastResult && (
          <>
            <Separator />
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium">Processing Results</h4>
                {lastResult.poses.length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowPoseDetails(!showPoseDetails)}
                    className="gap-1"
                  >
                    {showPoseDetails ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    {showPoseDetails ? 'Hide' : 'Show'} Poses
                  </Button>
                )}
              </div>

              {/* Statistics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="text-center p-2 bg-muted/50 rounded">
                  <div className="text-lg font-semibold text-primary">
                    {lastResult.poses.length}
                  </div>
                  <div className="text-xs text-muted-foreground">Poses Found</div>
                </div>

                <div className="text-center p-2 bg-muted/50 rounded">
                  <div className="text-lg font-semibold text-primary">
                    {Object.keys(getCharacterStats()).length}
                  </div>
                  <div className="text-xs text-muted-foreground">Characters</div>
                </div>

                {settings.includeEnhancement && (
                  <div className="text-center p-2 bg-muted/50 rounded">
                    <div className="text-lg font-semibold text-primary">
                      {lastResult.poses.filter(p => p.enhanced_text).length}
                    </div>
                    <div className="text-xs text-muted-foreground">Enhanced</div>
                  </div>
                )}


              </div>

              {/* Character Statistics */}
              {Object.keys(getCharacterStats()).length > 0 && (
                <div className="space-y-2">
                  <Label className="text-xs">Characters by Pose Count</Label>
                  <div className="flex flex-wrap gap-1">
                    {Object.entries(getCharacterStats())
                      .sort(([,a], [,b]) => b - a)
                      .map(([character, count]) => (
                      <Badge key={character} variant="secondary" className="gap-1 text-xs">
                        <Users className="h-3 w-3" />
                        {character}: {count}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Detailed Pose List */}
              {showPoseDetails && lastResult.poses.length > 0 && (
                <div className="space-y-2">
                  <Label className="text-xs">Extracted Poses</Label>
                  <ScrollArea className="h-48 w-full border rounded">
                    <div className="p-3 space-y-2">
                      {lastResult.poses.map((pose, index) => (
                        <div key={index} className="p-2 bg-muted/30 rounded text-xs space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-medium">{pose.character_name}</span>
                            <Badge variant="outline" className="text-xs">
                              {formatPoseType(pose.pose_type)}
                            </Badge>
                          </div>
                          <div className="text-muted-foreground line-clamp-2">
                            {pose.enhanced_text || pose.pose_text}
                          </div>
                          {pose.mentions && pose.mentions.length > 0 && (
                            <div className="flex gap-1">
                              {pose.mentions.map((mention, i) => (
                                <Badge key={i} variant="secondary" className="text-xs">
                                  @{mention}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              )}
            </div>
          </>
        )}

        {/* Status Messages */}
        {!veniceApiKey && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Venice API key is required for scene dump processing.
            </AlertDescription>
          </Alert>
        )}

        {!sceneDumpText?.trim() && veniceApiKey && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Add content to the scene dump area to begin processing.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  )
} 