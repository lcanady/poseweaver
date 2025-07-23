"use client"

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  Users, 
  MapPin, 
  Flag, 
  Activity,
  RefreshCw,
  Settings,
  Eye,
  EyeOff,
  Loader2,
  TrendingUp,
  Clock,
  Target,
  Zap
} from 'lucide-react'
import { cn } from '@/lib/utils'

import { ContinuityAlertsDisplay } from './continuity-alerts-display'
import { ContinuityFlagManager } from './continuity-flag-manager'
import { CharacterStateDisplay } from './character-state-display'
import { EnvironmentStateDisplay } from './environment-state-display'

import type { 
  ContinuityDashboardProps,
  ContinuitySummary,
  ContinuityFlag,
  ContinuityWarning,
  CharacterState,
  EnvironmentState,
  ContinuityAnalysis
} from '@/types/continuity'

interface DashboardState {
  summary: ContinuitySummary | null
  flags: ContinuityFlag[]
  warnings: ContinuityWarning[]
  characterStates: CharacterState[]
  environmentStates: EnvironmentState[]
  loading: boolean
  error: string | null
  lastUpdate: string | null
  autoRefresh: boolean
  refreshInterval: number
  realTimeAlerts: boolean
}

export function ContinuityDashboard({
  scene_id,
  scene_name,
  onFlagResolve,
  onCharacterStateUpdate,
  onEnvironmentStateUpdate,
  onAnalyzeContent,
  showRealTimeAlerts = true,
  showFlagManagement = true,
  showCharacterStates = true,
  showEnvironmentStates = true,
  autoRefresh = true,
  refreshInterval = 30000
}: ContinuityDashboardProps) {
  const [dashboardState, setDashboardState] = useState<DashboardState>({
    summary: null,
    flags: [],
    warnings: [],
    characterStates: [],
    environmentStates: [],
    loading: false,
    error: null,
    lastUpdate: null,
    autoRefresh,
    refreshInterval,
    realTimeAlerts: showRealTimeAlerts
  })

  const [activeTab, setActiveTab] = useState('overview')
  const [showSettings, setShowSettings] = useState(false)

  // Load continuity data
  const loadContinuityData = useCallback(async () => {
    setDashboardState(prev => ({ ...prev, loading: true, error: null }))
    
    try {
      const token = localStorage.getItem('access_token')
      const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }

      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'

      // Load summary
      const summaryResponse = await fetch(`${baseUrl}/api/continuity/summary/${scene_id}`, {
        headers
      })
      const summaryData = await summaryResponse.json()

      // Load flags
      const flagsResponse = await fetch(`${baseUrl}/api/continuity/flags?scene_id=${scene_id}&limit=100`, {
        headers
      })
      const flagsData = await flagsResponse.json()

      // Load character states
      const characterStatesResponse = await fetch(`${baseUrl}/api/continuity/character-states/${scene_id}`, {
        headers
      })
      const characterStatesData = await characterStatesResponse.json()

      // Load environment states
      const environmentStatesResponse = await fetch(`${baseUrl}/api/continuity/environment-states/${scene_id}`, {
        headers
      })
      const environmentStatesData = await environmentStatesResponse.json()

      // Generate warnings based on flags
      const warnings: ContinuityWarning[] = []
      if (flagsData.success && flagsData.data) {
        flagsData.data.forEach((flag: ContinuityFlag) => {
          if (!flag.resolved && (flag.severity === 'high' || flag.severity === 'critical')) {
            warnings.push({
              id: `flag-${flag.id}`,
              type: flag.flag_type.includes('character') ? 'character' : 
                    flag.flag_type.includes('environment') ? 'environment' : 'plot',
              severity: flag.severity === 'critical' ? 'error' : 'warning',
              title: flag.title,
              message: flag.description,
              suggestion: flag.suggestion,
              action_required: flag.severity === 'critical',
              dismissible: true,
              auto_dismiss_after: flag.severity === 'high' ? 30 : undefined
            })
          }
        })
      }

      setDashboardState(prev => ({
        ...prev,
        summary: summaryData.success ? summaryData.data : null,
        flags: flagsData.success ? flagsData.data : [],
        warnings,
        characterStates: characterStatesData.success ? characterStatesData.data : [],
        environmentStates: environmentStatesData.success ? environmentStatesData.data : [],
        loading: false,
        lastUpdate: new Date().toISOString(),
        error: null
      }))

    } catch (error) {
      console.error('Error loading continuity data:', error)
      setDashboardState(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to load continuity data. Please try again.'
      }))
    }
  }, [scene_id])

  // Set up auto-refresh
  useEffect(() => {
    if (dashboardState.autoRefresh) {
      const interval = setInterval(loadContinuityData, dashboardState.refreshInterval)
      return () => clearInterval(interval)
    }
  }, [dashboardState.autoRefresh, dashboardState.refreshInterval, loadContinuityData])

  // Initial load
  useEffect(() => {
    loadContinuityData()
  }, [loadContinuityData])

  // Handle flag resolution
  const handleFlagResolve = useCallback(async (flagId: string, resolution: string) => {
    try {
      const token = localStorage.getItem('access_token')
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'
      const response = await fetch(`${baseUrl}/api/continuity/flags/${flagId}/resolve`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ resolution_notes: resolution })
      })

      if (response.ok) {
        // Update local state
        setDashboardState(prev => ({
          ...prev,
          flags: prev.flags.map(flag => 
            flag.id === flagId 
              ? { ...flag, resolved: true, resolution_notes: resolution, resolved_at: new Date().toISOString() }
              : flag
          ),
          warnings: prev.warnings.filter(warning => warning.id !== `flag-${flagId}`)
        }))
        
        // Call parent handler
        onFlagResolve?.(flagId, resolution)
      }
    } catch (error) {
      console.error('Error resolving flag:', error)
    }
  }, [onFlagResolve])

  // Handle warning dismissal
  const handleWarningDismiss = useCallback((warningId: string) => {
    setDashboardState(prev => ({
      ...prev,
      warnings: prev.warnings.filter(warning => warning.id !== warningId)
    }))
  }, [])

  // Handle character state update
  const handleCharacterStateUpdate = useCallback(async (characterId: string, updates: Partial<CharacterState>) => {
    try {
      const token = localStorage.getItem('access_token')
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'
      const response = await fetch(`${baseUrl}/api/continuity/character-states/${scene_id}/${characterId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(updates)
      })

      if (response.ok) {
        // Update local state
        setDashboardState(prev => ({
          ...prev,
          characterStates: prev.characterStates.map(state => 
            state.character_id === characterId 
              ? { ...state, ...updates, last_updated: new Date().toISOString() }
              : state
          )
        }))
        
        // Call parent handler
        onCharacterStateUpdate?.(characterId, updates)
      }
    } catch (error) {
      console.error('Error updating character state:', error)
    }
  }, [scene_id, onCharacterStateUpdate])

  // Handle environment state update
  const handleEnvironmentStateUpdate = useCallback(async (environmentId: string, updates: Partial<EnvironmentState>) => {
    try {
      const token = localStorage.getItem('access_token')
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'
      const response = await fetch(`${baseUrl}/api/continuity/environment-states/${scene_id}/${environmentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(updates)
      })

      if (response.ok) {
        // Update local state
        setDashboardState(prev => ({
          ...prev,
          environmentStates: prev.environmentStates.map(state => 
            state.id === environmentId 
              ? { ...state, ...updates, last_updated: new Date().toISOString() }
              : state
          )
        }))
        
        // Call parent handler
        onEnvironmentStateUpdate?.(environmentId, updates)
      }
    } catch (error) {
      console.error('Error updating environment state:', error)
    }
  }, [scene_id, onEnvironmentStateUpdate])

  // Calculate summary stats
  const summaryStats = dashboardState.summary ? {
    totalFlags: dashboardState.summary.total_flags || 0,
    unresolvedFlags: dashboardState.summary.unresolved_flags || 0,
    overallScore: dashboardState.summary.overall_score || 0,
    criticalFlags: dashboardState.summary.severity_distribution?.critical || 0,
    highFlags: dashboardState.summary.severity_distribution?.high || 0,
    activeWarnings: dashboardState.warnings.length
  } : null

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600'
    if (score >= 70) return 'text-yellow-600'
    if (score >= 50) return 'text-orange-600'
    return 'text-red-600'
  }

  const getScoreBadgeVariant = (score: number) => {
    if (score >= 90) return 'default'
    if (score >= 70) return 'secondary'
    if (score >= 50) return 'outline'
    return 'destructive'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="h-6 w-6 text-primary" />
              <div>
                <CardTitle className="text-xl">Continuity Dashboard</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  {scene_name} {dashboardState.lastUpdate && `• Last updated: ${new Date(dashboardState.lastUpdate).toLocaleTimeString()}`}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSettings(!showSettings)}
              >
                <Settings className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={loadContinuityData}
                disabled={dashboardState.loading}
              >
                <RefreshCw className={cn("h-4 w-4", dashboardState.loading && "animate-spin")} />
              </Button>
            </div>
          </div>
        </CardHeader>
        
        {/* Settings Panel */}
        {showSettings && (
          <CardContent className="border-t">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="auto-refresh">Auto Refresh</Label>
                <Switch 
                  id="auto-refresh"
                  checked={dashboardState.autoRefresh}
                  onCheckedChange={(checked) => 
                    setDashboardState(prev => ({ ...prev, autoRefresh: checked }))
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="real-time-alerts">Real-time Alerts</Label>
                <Switch 
                  id="real-time-alerts"
                  checked={dashboardState.realTimeAlerts}
                  onCheckedChange={(checked) => 
                    setDashboardState(prev => ({ ...prev, realTimeAlerts: checked }))
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="refresh-interval">Refresh Interval (30s)</Label>
                <Switch 
                  id="refresh-interval"
                  checked={dashboardState.refreshInterval === 30000}
                  onCheckedChange={(checked) => 
                    setDashboardState(prev => ({ ...prev, refreshInterval: checked ? 30000 : 60000 }))
                  }
                />
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Real-time Alerts */}
      {dashboardState.realTimeAlerts && showRealTimeAlerts && dashboardState.warnings.length > 0 && (
        <ContinuityAlertsDisplay
          scene_id={scene_id}
          warnings={dashboardState.warnings}
          onDismiss={handleWarningDismiss}
          maxVisible={3}
          position="top"
          autoHide={true}
        />
      )}

      {/* Error Display */}
      {dashboardState.error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{dashboardState.error}</AlertDescription>
        </Alert>
      )}

      {/* Summary Stats */}
      {summaryStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Overall Score</p>
                  <p className={cn("text-2xl font-bold", getScoreColor(summaryStats.overallScore))}>
                    {summaryStats.overallScore}%
                  </p>
                </div>
                <Badge variant={getScoreBadgeVariant(summaryStats.overallScore)}>
                  <TrendingUp className="h-3 w-3 mr-1" />
                  {summaryStats.overallScore >= 90 ? 'Excellent' : 
                   summaryStats.overallScore >= 70 ? 'Good' : 
                   summaryStats.overallScore >= 50 ? 'Fair' : 'Poor'}
                </Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Unresolved Flags</p>
                  <p className="text-2xl font-bold">{summaryStats.unresolvedFlags}</p>
                </div>
                <Flag className="h-5 w-5 text-yellow-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Active Warnings</p>
                  <p className="text-2xl font-bold">{summaryStats.activeWarnings}</p>
                </div>
                <AlertTriangle className="h-5 w-5 text-orange-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Critical Issues</p>
                  <p className="text-2xl font-bold text-red-600">{summaryStats.criticalFlags}</p>
                </div>
                <Zap className="h-5 w-5 text-red-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="flags" disabled={!showFlagManagement}>
            <Flag className="h-4 w-4 mr-2" />
            Flags ({dashboardState.flags.filter(f => !f.resolved).length})
          </TabsTrigger>
          <TabsTrigger value="characters" disabled={!showCharacterStates}>
            <Users className="h-4 w-4 mr-2" />
            Characters ({dashboardState.characterStates.length})
          </TabsTrigger>
          <TabsTrigger value="environment" disabled={!showEnvironmentStates}>
            <MapPin className="h-4 w-4 mr-2" />
            Environment ({dashboardState.environmentStates.length})
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {dashboardState.loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : dashboardState.summary ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Flag Distribution */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Flag Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries((dashboardState.summary as any).flag_types || {}).map(([type, count]) => (
                      <div key={type} className="flex items-center justify-between">
                        <span className="text-sm font-medium capitalize">
                          {type.replace('_', ' ')}
                        </span>
                        <Badge variant="outline">{count as number}</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Severity Distribution */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Severity Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(dashboardState.summary.severity_distribution || {}).map(([severity, count]) => (
                      <div key={severity} className="flex items-center justify-between">
                        <span className="text-sm font-medium capitalize">{severity}</span>
                        <Badge 
                          variant={
                            severity === 'critical' ? 'destructive' :
                            severity === 'high' ? 'secondary' :
                            severity === 'medium' ? 'outline' : 'default'
                          }
                        >
                          {count as number}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Recent Activity */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Recent Activity (24h)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">New Flags</span>
                      <Badge variant="outline">{dashboardState.summary.recent_activity?.new_flags_24h || 0}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Resolved Flags</span>
                      <Badge variant="outline">{dashboardState.summary.recent_activity?.resolved_flags_24h || 0}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Analyses Run</span>
                      <Badge variant="outline">{dashboardState.summary.recent_activity?.analysis_count_24h || 0}</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Recommendations */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Recommendations</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {(dashboardState.summary.recommendations || []).map((recommendation, index) => (
                      <div key={index} className="flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <span className="text-sm">{recommendation}</span>
                      </div>
                    ))}
                    {(!dashboardState.summary.recommendations || dashboardState.summary.recommendations.length === 0) && (
                      <div className="flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <span className="text-sm">No specific recommendations at this time</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <div className="text-center py-8">
              <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Summary Available</h3>
              <p className="text-muted-foreground">
                Continuity summary will appear here once data is available.
              </p>
            </div>
          )}
        </TabsContent>

        {/* Flags Tab */}
        <TabsContent value="flags">
          <ContinuityFlagManager
            scene_id={scene_id}
            flags={dashboardState.flags}
            onResolve={handleFlagResolve}
            showResolved={true}
            showFilters={true}
            showBulkActions={true}
            paginate={true}
            pageSize={20}
          />
        </TabsContent>

        {/* Characters Tab */}
        <TabsContent value="characters">
          <CharacterStateDisplay
            character_states={dashboardState.characterStates}
            scene_id={scene_id}
            editable={true}
            onStateUpdate={handleCharacterStateUpdate}
            showRelationships={true}
            showPlotKnowledge={true}
            showHistory={true}
            compactView={false}
          />
        </TabsContent>

        {/* Environment Tab */}
        <TabsContent value="environment">
          <EnvironmentStateDisplay
            environment_states={dashboardState.environmentStates}
            scene_id={scene_id}
            editable={true}
            onStateUpdate={handleEnvironmentStateUpdate}
            showInteractiveElements={true}
            showOccupants={true}
            showHistory={true}
            compactView={false}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
} 