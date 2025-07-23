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
  Brain,
  Eye,
  EyeOff
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useSceneDumpProcessor } from '@/hooks/useSceneDumpProcessor'
import { useAuth } from '@/contexts/auth-context'
import type { ProcessedPose, SceneDumpProcessingResult } from '@/hooks/useSceneDumpProcessor'

interface SceneDumpProcessorProps {
  sceneDumpText: string
  sceneId?: string
  sceneTitle?: string
  onProcessingComplete?: (result: SceneDumpProcessingResult) => void
  autoProcess?: boolean
  className?: string
}

export function SceneDumpProcessor({
  sceneDumpText,
  sceneId,
  sceneTitle,
  onProcessingComplete,
  autoProcess = false,
  className
}: SceneDumpProcessorProps) {
  const { 
    processSceneDump, 
    isProcessing, 
    lastResult, 
    error, 
    clearError 
  } = useSceneDumpProcessor()
  
  const { isLoading: authLoading, isAuthenticated, user, refreshUser } = useAuth()

  // Client-side token state
  const [tokenInfo, setTokenInfo] = useState({
    hasAccessToken: false,
    hasRefreshToken: false,
    mounted: false
  })

  // Update token info on client side only
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setTokenInfo({
        hasAccessToken: !!localStorage.getItem('access_token'),
        hasRefreshToken: !!localStorage.getItem('refresh_token'),
        mounted: true
      })
    }
  }, [isAuthenticated, user])

  const [settings, setSettings] = useState({
    autoProcess: autoProcess,
    processingFormat: 'mush_output' as 'simple' | 'character_prefix' | 'mush_output' | 'discord',
    includeEnhancement: false,
    includeContinuityAnalysis: true
  })

  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false)
  const [showPoseDetails, setShowPoseDetails] = useState(false)

  // Auto-process when enabled and scene dump text changes, but only if authenticated
  useEffect(() => {
    if (settings.autoProcess && sceneDumpText?.trim() && sceneId && !isProcessing && !authLoading && isAuthenticated) {
      handleProcess()
    }
  }, [sceneDumpText, sceneId, settings.autoProcess, authLoading, isAuthenticated])

  const handleProcess = async () => {
    if (!sceneDumpText?.trim()) {
      return
    }

    const result = await processSceneDump(sceneDumpText, sceneId, {
      processingFormat: settings.processingFormat,
      includeEnhancement: settings.includeEnhancement,
      includeContinuityAnalysis: settings.includeContinuityAnalysis
    })

    if (onProcessingComplete) {
      onProcessingComplete(result)
    }
  }

  const handleRefreshAuth = async () => {
    try {
      await refreshUser()
      // Update token info after refresh
      if (typeof window !== 'undefined') {
        setTokenInfo({
          hasAccessToken: !!localStorage.getItem('access_token'),
          hasRefreshToken: !!localStorage.getItem('refresh_token'),
          mounted: true
        })
      }
    } catch (error) {
      console.error('Failed to refresh auth:', error)
    }
  }

  const handleClearTokensAndLogin = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
  }

  const getProcessingStatusBadge = () => {
    if (isProcessing) {
      return <Badge variant="secondary" className="gap-1">
        <Loader2 className="h-3 w-3 animate-spin" />
        Processing...
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
              Scene Dump Processor
            </CardTitle>
            <CardDescription>
              Process scene dump content and extract poses automatically
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
                {lastResult?.error && lastResult.error !== error && (
                  <div className="text-xs opacity-75">Details: {lastResult.error}</div>
                )}
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" onClick={clearError} className="w-fit">
                    <XCircle className="h-4 w-4" />
                    Dismiss
                  </Button>
                  {error.includes('log in') && (
                    <Button variant="ghost" size="sm" onClick={handleRefreshAuth} className="w-fit">
                      <RefreshCw className="h-4 w-4" />
                      Refresh Auth
                    </Button>
                  )}
                  {error.includes('not found') && sceneId && (
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={async () => {
                        // Test if scene exists
                        try {
                          const token = localStorage.getItem('access_token')
                          const response = await fetch(
                            `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/scenes/${sceneId}`,
                            {
                              headers: {
                                'Authorization': `Bearer ${token}`,
                                'Content-Type': 'application/json'
                              }
                            }
                          )
                          
                          if (response.ok) {
                            const data = await response.json()
                            console.log('Scene check successful:', data)
                            alert(`Scene exists: ${data.data?.name || 'Unknown'}`)
                          } else if (response.status === 404) {
                            console.log('Scene not found')
                            alert('Scene not found in database. You may need to save the scene first.')
                          } else if (response.status === 403) {
                            console.log('Access denied')
                            alert('Access denied to this scene. Check if you own this scene.')
                          } else {
                            const errorData = await response.json()
                            console.log('Scene check failed:', response.status, errorData)
                            alert(`Scene check failed: ${errorData.message || response.statusText}`)
                          }
                        } catch (error) {
                          console.error('Scene check error:', error)
                          alert('Failed to check scene status')
                        }
                      }} 
                      className="w-fit"
                    >
                      <AlertCircle className="h-4 w-4" />
                      Check Scene
                    </Button>
                  )}
                </div>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Scene ID Warning */}
        {sceneId && !error && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <div className="flex items-center justify-between">
                <div className="text-sm">
                  Scene ID: <code className="bg-muted px-1 rounded text-xs">{sceneId}</code>
                </div>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={async () => {
                    try {
                      const token = localStorage.getItem('access_token')
                      const response = await fetch(
                        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/scenes/${sceneId}`,
                        {
                          headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json'
                          }
                        }
                      )
                      
                      if (response.ok) {
                        const data = await response.json()
                        console.log('Scene validation successful:', data)
                      } else {
                        console.log('Scene validation failed:', response.status)
                      }
                    } catch (error) {
                      console.error('Scene validation error:', error)
                    }
                  }}
                  className="text-xs h-6"
                >
                  Validate Scene
                </Button>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Quick Actions */}
        <div className="flex flex-wrap items-center gap-3">
          <Button 
            onClick={handleProcess}
            disabled={isProcessing || !sceneDumpText?.trim() || !sceneId || authLoading || !isAuthenticated}
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

          {(!isAuthenticated || error?.includes('log in')) && (
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleRefreshAuth}
              disabled={authLoading}
              className="gap-1"
            >
              <RefreshCw className={cn("h-4 w-4", authLoading && "animate-spin")} />
              Refresh Auth
            </Button>
          )}

          {/* Test Authentication Button for debugging */}
          {process.env.NODE_ENV === 'development' && (
            <Button 
              variant="outline" 
              size="sm"
              onClick={async () => {
                console.log('=== AUTH TEST ===')
                console.log('authLoading:', authLoading)
                console.log('isAuthenticated:', isAuthenticated)
                console.log('user:', user)
                console.log('tokenInfo:', tokenInfo)
                
                // Test direct API call
                try {
                  const token = localStorage.getItem('access_token')
                  console.log('Direct token check:', !!token)
                  
                  if (token) {
                    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/auth/me`, {
                      headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                      }
                    })
                    console.log('API test response:', response.status, response.statusText)
                    if (response.ok) {
                      const data = await response.json()
                      console.log('API test data:', data)
                    }
                  }
                } catch (error) {
                  console.log('API test error:', error)
                }
                console.log('=== END AUTH TEST ===')
              }}
              className="gap-1 text-xs"
            >
              🧪 Test Auth
            </Button>
          )}
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
                      <SelectItem value="discord">Discord</SelectItem>
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
                  
                  <div className="flex items-center gap-2">
                    <Switch
                      id="continuity"
                      checked={settings.includeContinuityAnalysis}
                      onCheckedChange={(checked) => 
                        setSettings(prev => ({ ...prev, includeContinuityAnalysis: checked }))
                      }
                    />
                    <Label htmlFor="continuity" className="text-xs flex items-center gap-1">
                      <Brain className="h-3 w-3" />
                      Continuity Analysis
                    </Label>
                  </div>
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
                    {lastResult.importedCount}
                  </div>
                  <div className="text-xs text-muted-foreground">Poses Imported</div>
                </div>

                <div className="text-center p-2 bg-muted/50 rounded">
                  <div className="text-lg font-semibold text-primary">
                    {Object.keys(getCharacterStats()).length}
                  </div>
                  <div className="text-xs text-muted-foreground">Characters</div>
                </div>

                {settings.includeEnhancement && lastResult.enhancedPoses && (
                  <div className="text-center p-2 bg-muted/50 rounded">
                    <div className="text-lg font-semibold text-primary">
                      {lastResult.enhancedPoses.length}
                    </div>
                    <div className="text-xs text-muted-foreground">Enhanced</div>
                  </div>
                )}

                {settings.includeContinuityAnalysis && lastResult.continuityAnalysis && (
                  <div className="text-center p-2 bg-muted/50 rounded">
                    <div className="text-lg font-semibold text-primary">
                      <Brain className="h-5 w-5 mx-auto" />
                    </div>
                    <div className="text-xs text-muted-foreground">Analyzed</div>
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
                            {pose.pose_text.substring(0, 100)}
                            {pose.pose_text.length > 100 && '...'}
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
        {authLoading && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Loading authentication status...
            </AlertDescription>
          </Alert>
        )}
        
        {!authLoading && !isAuthenticated && tokenInfo.mounted && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <div className="space-y-2">
                <div>Please log in to use scene dump processing.</div>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={handleClearTokensAndLogin}
                    className="w-fit"
                  >
                    Go to Login
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={handleRefreshAuth}
                    disabled={authLoading}
                    className="w-fit"
                  >
                    <RefreshCw className={cn("h-4 w-4", authLoading && "animate-spin")} />
                    Try Refresh
                  </Button>
                </div>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {!sceneId && isAuthenticated && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Save your scene first to enable automatic pose processing.
            </AlertDescription>
          </Alert>
        )}

        {!sceneDumpText?.trim() && isAuthenticated && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Add content to the scene dump area to begin processing.
            </AlertDescription>
          </Alert>
        )}

        {/* Debug Info (only in development) */}
        {process.env.NODE_ENV === 'development' && tokenInfo.mounted && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <details className="text-xs">
                <summary className="cursor-pointer font-medium">Debug Info</summary>
                <div className="mt-2 space-y-1">
                  <div>Auth Loading: {authLoading ? 'Yes' : 'No'}</div>
                  <div>Authenticated: {isAuthenticated ? 'Yes' : 'No'}</div>
                  <div>User ID: {user?.id || 'None'}</div>
                  <div>User _ID: {user?._id || 'None'}</div>
                  <div>User Email: {user?.email || 'None'}</div>
                  <div>Has Access Token: {tokenInfo.hasAccessToken ? 'Yes' : 'No'}</div>
                  <div>Has Refresh Token: {tokenInfo.hasRefreshToken ? 'Yes' : 'No'}</div>
                  <div>Scene ID: {sceneId || 'None'}</div>
                  <div>Scene Dump Length: {sceneDumpText?.length || 0}</div>
                  <div className="pt-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => {
                        console.log('Auth Debug Info:', {
                          authLoading,
                          isAuthenticated,
                          user,
                          tokenInfo,
                          sceneId,
                          sceneDumpLength: sceneDumpText?.length
                        })
                      }}
                      className="text-xs h-6"
                    >
                      Log Debug Info
                    </Button>
                  </div>
                </div>
              </details>
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  )
} 