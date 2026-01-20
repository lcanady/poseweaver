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
  Eye,
  EyeOff,
  Wand2,
  Settings2,
  Trash2,
  ChevronDown,
  ChevronUp,
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
  Sparkles
} from 'lucide-react'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { cn } from '../lib/utils'
import { OpenRouterClient, type ProcessedPose, type SceneDumpProcessingResult as OpenRouterProcessingResult } from '@/hooks/useSceneDumpProcessor'

interface StandaloneSceneDumpProcessorProps {
  // Required props
  openrouterApiKey: string
  userId: string
  userDisplayName: string
  sceneId?: string
  sceneTitle?: string
  className?: string

  // Optional configuration
  autoProcess?: boolean
  onProcessingComplete?: (result: OpenRouterProcessingResult & { sceneId?: string }) => void
  onSaveToScene?: (poses: ProcessedPose[], sceneId: string) => Promise<boolean>
}

export function StandaloneSceneDumpProcessor({
  openrouterApiKey,
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
  const [lastResult, setLastResult] = useState<OpenRouterProcessingResult & { sceneId?: string } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  const [settings, setSettings] = useState({
    autoProcess: true, // Default to true for "Don't Make Me Think"
    processingFormat: 'mush_output' as 'simple' | 'character_prefix' | 'mush_output',
    includeEnhancement: true, // Also default to true as it's a primary value prop
    enhancementStyle: 'balanced' as 'balanced' | 'dramatic' | 'subtle',
  })

  // Update settings if autoProcess prop changes
  useEffect(() => {
    if (autoProcess !== undefined) {
      setSettings(prev => ({ ...prev, autoProcess }))
    }
  }, [autoProcess])

  const [showPoseDetails, setShowPoseDetails] = useState(false)

  // Initialize OpenRouter client
  const openrouterClient = new OpenRouterClient(openrouterApiKey)

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

    if (!openrouterApiKey) {
      setError('OpenRouter API key is required for processing')
      return
    }

    setIsProcessing(true)
    setError(null)

    try {
      // Extract character name from user display name or scene dump
      const characterName = extractCharacterName(sceneDumpText, userDisplayName)

      // Process the scene dump using OpenRouter client
      const result = await openrouterClient.processSceneDump(
        sceneDumpText,
        characterName,
        {
          apiKey: openrouterApiKey,
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
        importedCount: 0,
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

  const resetAll = () => {
    setSceneDumpText('')
    setLastResult(null)
    setError(null)
    setShowPoseDetails(false)
  }

  const clearError = () => {
    setError(null)
  }

  const getProcessingStatusBadge = () => {
    if (isProcessing || isSaving) {
      return (
        <Badge variant="secondary" className="gap-1.5 h-6 px-2 text-[10px] font-bold uppercase tracking-wider animate-pulse">
          <Loader2 className="h-3 w-3 animate-spin" />
          {isProcessing ? 'Processing' : 'Saving'}
        </Badge>
      )
    }

    if (error) {
      return (
        <Badge variant="destructive" className="gap-1.5 h-6 px-2 text-[10px] font-bold uppercase tracking-wider">
          <XCircle className="h-3 w-3" />
          Error
        </Badge>
      )
    }

    if (lastResult?.success) {
      return (
        <Badge variant="default" className="gap-1.5 h-6 px-2 text-[10px] font-bold uppercase tracking-wider bg-green-600 hover:bg-green-600">
          <CheckCircle className="h-3 w-3" />
          Success
        </Badge>
      )
    }

    return (
      <Badge variant="outline" className="gap-1.5 h-6 px-2 text-[10px] font-bold uppercase tracking-wider opacity-50">
        <Clock className="h-3 w-3" />
        Idle
      </Badge>
    )
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
    <Card className={cn("overflow-hidden border-2 transition-all duration-300",
      isProcessing ? "border-primary/50 shadow-lg shadow-primary/10" : "border-border",
      className)}>
      <CardHeader className="bg-muted/30 pb-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2 text-xl font-bold tracking-tight">
              <div className="bg-primary/10 p-1.5 rounded-lg text-primary">
                <Wand2 className="h-5 w-5" />
              </div>
              Scene Dump Magic
            </CardTitle>
            <CardDescription className="text-sm font-medium">
              Paste your scene and let the AI extract the poses automatically.
            </CardDescription>
          </div>
          {getProcessingStatusBadge()}
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div className="grid grid-cols-1 divide-y">
          {/* Main Input Section */}
          <div className="p-4 space-y-4">
            {/* Error Display */}
            {error && (
              <Alert variant="destructive" className="animate-in fade-in slide-in-from-top-2">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription className="flex items-center justify-between gap-4">
                  <span className="text-sm">{error}</span>
                  <Button variant="ghost" size="sm" onClick={clearError} className="h-7 px-2">
                    Dismiss
                  </Button>
                </AlertDescription>
              </Alert>
            )}

            <div className="relative group">
              <Textarea
                id="scene-dump"
                placeholder="Paste your MUSH/Discord scene dump here..."
                value={sceneDumpText}
                onChange={(e) => setSceneDumpText(e.target.value)}
                rows={10}
                className={cn(
                  "font-mono text-sm resize-none focus-visible:ring-1 transition-all",
                  "bg-background/50 group-hover:bg-background border-muted-foreground/20",
                  isProcessing && "opacity-50 pointer-events-none"
                )}
              />

              {!sceneDumpText && !isProcessing && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="flex flex-col items-center gap-2 text-muted-foreground/40">
                    <Upload className="h-8 w-8" />
                    <span className="text-xs font-medium uppercase tracking-widest">Ready for input</span>
                  </div>
                </div>
              )}

              {isProcessing && (
                <div className="absolute inset-0 flex items-center justify-center bg-background/20 backdrop-blur-[1px]">
                  <div className="flex flex-col items-center gap-3 p-4 rounded-xl bg-background shadow-2xl border animate-in zoom-in-95">
                    <div className="relative">
                      <Loader2 className="h-8 w-8 animate-spin text-primary" />
                      <Sparkles className="h-4 w-4 absolute -top-1 -right-1 text-yellow-500 animate-pulse" />
                    </div>
                    <span className="text-sm font-bold tracking-tight px-2">Processing Magic...</span>
                  </div>
                </div>
              )}
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {!isProcessing && sceneDumpText && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={resetAll}
                    className="h-8 text-xs font-medium gap-1.5 text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Clear
                  </Button>
                )}
              </div>

              {!settings.autoProcess && !isProcessing && (
                <Button
                  onClick={handleProcess}
                  disabled={!sceneDumpText?.trim()}
                  className="gap-2 shadow-sm font-bold active:scale-95 transition-transform"
                >
                  <Wand2 className="h-4 w-4" />
                  Process Poses
                </Button>
              )}
            </div>
          </div>

          {/* Settings Section (Progressive Disclosure) */}
          <div className="bg-muted/20">
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="settings" className="border-none">
                <AccordionTrigger className="px-4 py-2 hover:no-underline hover:bg-muted/30 text-xs font-semibold text-muted-foreground uppercase tracking-widest">
                  <div className="flex items-center gap-2">
                    <Settings2 className="h-3.5 w-3.5" />
                    Magic Settings
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-4 pb-4 space-y-4 animate-in fade-in-50">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="auto-process" className="text-sm font-bold">Auto-process</Label>
                        <Switch
                          id="auto-process"
                          checked={settings.autoProcess}
                          onCheckedChange={(checked) =>
                            setSettings(prev => ({ ...prev, autoProcess: checked }))
                          }
                        />
                      </div>
                      <p className="text-[10px] text-muted-foreground leading-relaxed">
                        Starts processing immediately when you finish pasting text.
                      </p>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="enhancement" className="text-sm font-bold flex items-center gap-1.5">
                          <Sparkles className="h-3.5 w-3.5 text-yellow-600" />
                          AI Enhancement
                        </Label>
                        <Switch
                          id="enhancement"
                          checked={settings.includeEnhancement}
                          onCheckedChange={(checked) =>
                            setSettings(prev => ({ ...prev, includeEnhancement: checked }))
                          }
                        />
                      </div>
                      <p className="text-[10px] text-muted-foreground leading-relaxed">
                        Refine the writing quality of extracted poses using AI.
                      </p>
                    </div>
                  </div>

                  <Separator className="opacity-50" />

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <Label className="text-xs font-bold">Input Format</Label>
                      <Select
                        value={settings.processingFormat}
                        onValueChange={(value: any) =>
                          setSettings(prev => ({ ...prev, processingFormat: value }))
                        }
                      >
                        <SelectTrigger className="h-9 bg-background/50">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="mush_output">MUSH Standard</SelectItem>
                          <SelectItem value="character_prefix">Labelled (Name: Pose)</SelectItem>
                          <SelectItem value="simple">Freeform/Simple</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {settings.includeEnhancement && (
                      <div className="space-y-2">
                        <Label className="text-xs font-bold">Enhancement Style</Label>
                        <Select
                          value={settings.enhancementStyle}
                          onValueChange={(value: any) =>
                            setSettings(prev => ({ ...prev, enhancementStyle: value }))
                          }
                        >
                          <SelectTrigger className="h-9 bg-background/50">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="balanced">Balanced</SelectItem>
                            <SelectItem value="dramatic">Dramatic & Flowery</SelectItem>
                            <SelectItem value="subtle">Subtle Cleanup</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    )}
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </div>

          {/* Results Section */}
          {lastResult && (
            <div className="p-4 bg-primary/[0.02] border-t-2 border-primary/20 space-y-4 animate-in slide-in-from-bottom-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 p-1.5 rounded-full">
                    <CheckCircle className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-base font-bold tracking-tight">Processing Complete</h4>
                    <p className="text-xs text-muted-foreground">Successfully extracted {lastResult.poses.length} poses.</p>
                  </div>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowPoseDetails(!showPoseDetails)}
                  className="h-8 text-xs gap-1.5 font-bold"
                >
                  {showPoseDetails ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                  {showPoseDetails ? 'Hide' : 'Review'} Poses
                </Button>
              </div>

              {/* Statistics & Preview Toggle Area */}
              {showPoseDetails && (
                <div className="pt-2 space-y-4 animate-in fade-in zoom-in-95 duration-200">
                  {/* Character Stats Chips */}
                  {Object.keys(getCharacterStats()).length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {Object.entries(getCharacterStats())
                        .sort(([, a], [, b]) => (b as number) - (a as number))
                        .map(([character, count]) => (
                          <Badge key={character} variant="secondary" className="px-2 py-0.5 h-6 rounded-md text-[10px] font-bold bg-background shadow-xs border-[#e2e8f0] dark:border-[#1e293b]">
                            {character} · {count as number}
                          </Badge>
                        ))}
                    </div>
                  )}

                  <ScrollArea className="h-64 rounded-xl border bg-background/50 shadow-inner">
                    <div className="p-4 space-y-3">
                      {lastResult.poses.map((pose, index) => (
                        <div key={index} className="group relative p-3 rounded-lg border bg-background hover:border-primary/30 transition-colors">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-bold text-primary tracking-tight">
                              {pose.character_name}
                            </span>
                            <Badge variant="outline" className="text-[9px] font-black uppercase tracking-tighter h-5 px-1 bg-muted/30">
                              {formatPoseType(pose.pose_type)}
                            </Badge>
                          </div>
                          <div className="text-[13px] leading-relaxed text-foreground/90">
                            {pose.enhanced_text || pose.pose_text}
                          </div>
                          {pose.mentions && pose.mentions.length > 0 && (
                            <div className="flex gap-1 mt-2.5">
                              {pose.mentions.map((mention, i) => (
                                <span key={i} className="text-[10px] font-bold text-primary/70">
                                  @{mention}
                                </span>
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
          )}
        </div>
      </CardContent>

      {/* Footer Info */}
      {!openrouterApiKey && (
        <div className="px-4 py-2 bg-destructive/5 text-[10px] text-destructive font-bold text-center border-t border-destructive/10">
          OpenRouter API key missing. Processing will be disabled.
        </div>
      )}
    </Card>
  )
}
