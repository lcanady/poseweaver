"use client"

import { useState, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Eye, 
  ExternalLink,
  Brain,
  Activity,
  User,
  Target,
  Award,
  AlertCircle,
  Zap,
  FileText,
  Lightbulb
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { format } from 'date-fns'
import { useToast } from '@/hooks/use-toast'

import type { CharacterConsistencyScoreProps } from '@/types/character-tracking'

interface ResolutionDialogState {
  open: boolean
  inconsistency: any | null
  resolution: string
  submitting: boolean
}

export function CharacterConsistencyScoreDisplay({
  character_id,
  character_name,
  consistency_score,
  recent_inconsistencies,
  onInconsistencyClick
}: CharacterConsistencyScoreProps) {
  const [resolutionDialog, setResolutionDialog] = useState<ResolutionDialogState>({
    open: false,
    inconsistency: null,
    resolution: '',
    submitting: false
  })
  
  const { toast } = useToast()

  const getScoreColor = (score: number): string => {
    if (score >= 90) return 'text-green-600'
    if (score >= 80) return 'text-blue-600'
    if (score >= 70) return 'text-yellow-600'
    if (score >= 60) return 'text-orange-600'
    return 'text-red-600'
  }

  const getScoreBadgeVariant = (score: number) => {
    if (score >= 90) return 'default'
    if (score >= 80) return 'secondary'
    if (score >= 70) return 'outline'
    return 'destructive'
  }

  const getScoreLabel = (score: number): string => {
    if (score >= 95) return 'Excellent'
    if (score >= 90) return 'Very Good'
    if (score >= 80) return 'Good'
    if (score >= 70) return 'Fair'
    if (score >= 60) return 'Poor'
    return 'Critical'
  }

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'high': return 'text-red-600'
      case 'medium': return 'text-yellow-600'
      case 'low': return 'text-blue-600'
      default: return 'text-gray-600'
    }
  }

  const getSeverityBadgeVariant = (severity: string) => {
    switch (severity) {
      case 'high': return 'destructive'
      case 'medium': return 'outline'
      case 'low': return 'secondary'
      default: return 'secondary'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high': return <AlertTriangle className="h-3 w-3" />
      case 'medium': return <AlertCircle className="h-3 w-3" />
      case 'low': return <Lightbulb className="h-3 w-3" />
      default: return <AlertCircle className="h-3 w-3" />
    }
  }

  const handleResolveInconsistency = useCallback(async (inconsistency: any) => {
    setResolutionDialog({
      open: true,
      inconsistency,
      resolution: '',
      submitting: false
    })
  }, [])

  const submitResolution = useCallback(async () => {
    if (!resolutionDialog.inconsistency || !resolutionDialog.resolution.trim()) {
      toast({
        title: "Resolution Required",
        description: "Please provide a resolution explanation.",
        variant: "destructive"
      })
      return
    }

    setResolutionDialog(prev => ({ ...prev, submitting: true }))

    try {
      const token = localStorage.getItem('access_token')
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'
      
      const response = await fetch(`${baseUrl}/api/character-plot-tracking/resolve-inconsistency`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          character_id,
          inconsistency_id: resolutionDialog.inconsistency.id,
          resolution: resolutionDialog.resolution
        })
      })

      if (response.ok) {
        toast({
          title: "Inconsistency Resolved",
          description: "The inconsistency has been marked as resolved.",
        })
        
        // Close dialog and refresh
        setResolutionDialog({
          open: false,
          inconsistency: null,
          resolution: '',
          submitting: false
        })
        
        // Optionally trigger a refresh of the parent component
        window.location.reload()
      } else {
        throw new Error('Failed to resolve inconsistency')
      }
    } catch (error) {
      console.error('Error resolving inconsistency:', error)
      toast({
        title: "Resolution Failed",
        description: "Failed to resolve inconsistency. Please try again.",
        variant: "destructive"
      })
    } finally {
      setResolutionDialog(prev => ({ ...prev, submitting: false }))
    }
  }, [resolutionDialog, character_id, toast])

  const unresolvedInconsistencies = recent_inconsistencies.filter(inc => !inc.resolved)
  const resolvedInconsistencies = recent_inconsistencies.filter(inc => inc.resolved)

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-bold flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary" />
            Character Consistency
            <Badge variant="outline" className="ml-2">{character_name}</Badge>
          </CardTitle>
          
          <div className="flex items-center gap-3">
            <Badge variant={getScoreBadgeVariant(consistency_score)} className="px-3 py-1">
              <Target className="h-3 w-3 mr-1" />
              {getScoreLabel(consistency_score)}
            </Badge>
            <div className="text-right">
              <div className={cn("text-2xl font-bold", getScoreColor(consistency_score))}>
                {consistency_score}%
              </div>
              <p className="text-xs text-muted-foreground">Consistency Score</p>
            </div>
          </div>
        </div>
        
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Overall Consistency</span>
            <span className={cn("text-sm font-medium", getScoreColor(consistency_score))}>
              {consistency_score}/100
            </span>
          </div>
          <Progress value={consistency_score} className="h-2" />
        </div>
      </CardHeader>

      <CardContent>
        <Tabs defaultValue="unresolved" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="unresolved" className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Active Issues ({unresolvedInconsistencies.length})
            </TabsTrigger>
            <TabsTrigger value="resolved" className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4" />
              Resolved ({resolvedInconsistencies.length})
            </TabsTrigger>
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Overview
            </TabsTrigger>
          </TabsList>

          {/* Unresolved Issues */}
          <TabsContent value="unresolved" className="space-y-4 mt-4">
            {unresolvedInconsistencies.length > 0 ? (
              <div className="space-y-3">
                {unresolvedInconsistencies.map((inconsistency, index) => (
                  <Card key={index} className="border-l-4 border-l-red-500">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge variant={getSeverityBadgeVariant(inconsistency.severity)} className="flex items-center gap-1">
                            {getSeverityIcon(inconsistency.severity)}
                            {inconsistency.severity.toUpperCase()}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {format(new Date(inconsistency.timestamp), 'MMM d, h:mm a')}
                          </span>
                        </div>
                        <div className="flex gap-1">
                          {inconsistency.pose_id && (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-8 w-8 p-0"
                                    onClick={() => onInconsistencyClick?.(inconsistency)}
                                  >
                                    <Eye className="h-4 w-4" />
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>View Pose</TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          )}
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleResolveInconsistency(inconsistency)}
                          >
                            <CheckCircle className="h-4 w-4 mr-1" />
                            Resolve
                          </Button>
                        </div>
                      </div>
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        {inconsistency.description}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Active Issues</h3>
                <p className="text-muted-foreground">
                  This character has no unresolved consistency issues.
                </p>
              </div>
            )}
          </TabsContent>

          {/* Resolved Issues */}
          <TabsContent value="resolved" className="space-y-4 mt-4">
            {resolvedInconsistencies.length > 0 ? (
              <div className="space-y-3">
                {resolvedInconsistencies.map((inconsistency, index) => (
                  <Card key={index} className="border-l-4 border-l-green-500 opacity-75">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary" className="flex items-center gap-1">
                            <CheckCircle className="h-3 w-3" />
                            RESOLVED
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {inconsistency.severity}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {format(new Date(inconsistency.timestamp), 'MMM d, h:mm a')}
                          </span>
                        </div>
                        {inconsistency.pose_id && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={() => onInconsistencyClick?.(inconsistency)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {inconsistency.description}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Resolved Issues</h3>
                <p className="text-muted-foreground">
                  No consistency issues have been resolved yet.
                </p>
              </div>
            )}
          </TabsContent>

          {/* Overview */}
          <TabsContent value="overview" className="space-y-4 mt-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Total Issues</p>
                      <p className="text-2xl font-bold">{recent_inconsistencies.length}</p>
                    </div>
                    <Activity className="h-5 w-5 text-blue-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Active Issues</p>
                      <p className="text-2xl font-bold text-red-600">{unresolvedInconsistencies.length}</p>
                    </div>
                    <AlertTriangle className="h-5 w-5 text-red-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Resolution Rate</p>
                      <p className="text-2xl font-bold text-green-600">
                        {recent_inconsistencies.length > 0 
                          ? Math.round((resolvedInconsistencies.length / recent_inconsistencies.length) * 100)
                          : 100}%
                      </p>
                    </div>
                    <Award className="h-5 w-5 text-green-500" />
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Consistency Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">High Severity Issues</span>
                    <span className="text-sm text-red-600">
                      {recent_inconsistencies.filter(i => i.severity === 'high').length}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Medium Severity Issues</span>
                    <span className="text-sm text-yellow-600">
                      {recent_inconsistencies.filter(i => i.severity === 'medium').length}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Low Severity Issues</span>
                    <span className="text-sm text-blue-600">
                      {recent_inconsistencies.filter(i => i.severity === 'low').length}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </CardContent>

      {/* Resolution Dialog */}
      <Dialog open={resolutionDialog.open} onOpenChange={(open) => 
        setResolutionDialog(prev => ({ ...prev, open }))
      }>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Resolve Inconsistency</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {resolutionDialog.inconsistency && (
              <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-md">
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  {resolutionDialog.inconsistency.description}
                </p>
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="resolution">Resolution Explanation</Label>
              <Textarea
                id="resolution"
                placeholder="Explain how this inconsistency was resolved..."
                value={resolutionDialog.resolution}
                onChange={(e) => setResolutionDialog(prev => ({ 
                  ...prev, 
                  resolution: e.target.value 
                }))}
                className="min-h-20"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setResolutionDialog(prev => ({ ...prev, open: false }))}
              disabled={resolutionDialog.submitting}
            >
              Cancel
            </Button>
            <Button
              onClick={submitResolution}
              disabled={!resolutionDialog.resolution.trim() || resolutionDialog.submitting}
            >
              {resolutionDialog.submitting ? (
                <>
                  <Zap className="h-4 w-4 mr-2 animate-spin" />
                  Resolving...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Resolve
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
} 