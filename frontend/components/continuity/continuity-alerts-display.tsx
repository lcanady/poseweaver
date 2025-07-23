"use client"

import { useState, useEffect, useCallback } from 'react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  AlertTriangle, 
  X, 
  CheckCircle, 
  Info, 
  AlertCircle,
  Zap,
  Clock,
  Eye,
  EyeOff,
  ChevronUp,
  ChevronDown
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'

import type { ContinuityAlertsProps, ContinuityWarning } from '@/types/continuity'

interface AlertState {
  id: string
  dismissedAt?: string
  autoDismissTimer?: NodeJS.Timeout
  expanded: boolean
}

export function ContinuityAlertsDisplay({
  scene_id,
  warnings,
  onDismiss,
  onAction,
  maxVisible = 5,
  position = 'top',
  autoHide = true
}: ContinuityAlertsProps) {
  const [alertStates, setAlertStates] = useState<Record<string, AlertState>>({})
  const [collapsed, setCollapsed] = useState(false)
  const [showAll, setShowAll] = useState(false)
  const { toast } = useToast()

  // Initialize alert states
  useEffect(() => {
    const newStates: Record<string, AlertState> = {}
    
    warnings.forEach(warning => {
      if (!alertStates[warning.id]) {
        newStates[warning.id] = {
          id: warning.id,
          expanded: false
        }
        
        // Set up auto-dismiss timer if specified
        if (autoHide && warning.auto_dismiss_after) {
          const timer = setTimeout(() => {
            handleDismiss(warning.id, true)
          }, warning.auto_dismiss_after * 1000)
          
          newStates[warning.id].autoDismissTimer = timer
        }
      }
    })
    
    if (Object.keys(newStates).length > 0) {
      setAlertStates(prev => ({ ...prev, ...newStates }))
    }
  }, [warnings, autoHide])

  // Clean up timers on unmount
  useEffect(() => {
    return () => {
      Object.values(alertStates).forEach(state => {
        if (state.autoDismissTimer) {
          clearTimeout(state.autoDismissTimer)
        }
      })
    }
  }, [])

  const handleDismiss = useCallback((warningId: string, autoDismissed = false) => {
    // Clear auto-dismiss timer
    if (alertStates[warningId]?.autoDismissTimer) {
      clearTimeout(alertStates[warningId].autoDismissTimer)
    }
    
    // Update state
    setAlertStates(prev => ({
      ...prev,
      [warningId]: {
        ...prev[warningId],
        dismissedAt: new Date().toISOString(),
        autoDismissTimer: undefined
      }
    }))
    
    // Show toast for auto-dismissed alerts
    if (autoDismissed) {
      toast({
        title: "Alert Auto-dismissed",
        description: "A continuity alert was automatically dismissed.",
        variant: "default",
      })
    }
    
    // Call parent handler
    onDismiss?.(warningId)
  }, [alertStates, onDismiss, toast])

  const handleAction = useCallback((warningId: string, actionType: string) => {
    onAction?.(warningId, actionType)
  }, [onAction])

  const toggleExpanded = useCallback((warningId: string) => {
    setAlertStates(prev => ({
      ...prev,
      [warningId]: {
        ...prev[warningId],
        expanded: !prev[warningId]?.expanded
      }
    }))
  }, [])

  const getAlertVariant = (severity: string) => {
    switch (severity) {
      case 'error':
        return 'destructive'
      case 'warning':
        return 'default'
      case 'info':
        return 'default'
      default:
        return 'default'
    }
  }

  const getAlertIcon = (severity: string, type: string) => {
    if (severity === 'error') {
      return <AlertCircle className="h-4 w-4" />
    }
    if (severity === 'warning') {
      return <AlertTriangle className="h-4 w-4" />
    }
    if (type === 'timeline') {
      return <Clock className="h-4 w-4" />
    }
    return <Info className="h-4 w-4" />
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error':
        return 'text-red-600'
      case 'warning':
        return 'text-yellow-600'
      case 'info':
        return 'text-blue-600'
      default:
        return 'text-gray-600'
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'character':
        return 'bg-blue-100 text-blue-800'
      case 'environment':
        return 'bg-green-100 text-green-800'
      case 'plot':
        return 'bg-purple-100 text-purple-800'
      case 'timeline':
        return 'bg-orange-100 text-orange-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  // Filter out dismissed warnings
  const activeWarnings = warnings.filter(warning => 
    !alertStates[warning.id]?.dismissedAt
  )

  // Determine which warnings to show
  const visibleWarnings = showAll ? activeWarnings : activeWarnings.slice(0, maxVisible)
  const hiddenCount = activeWarnings.length - visibleWarnings.length

  if (activeWarnings.length === 0) {
    return null
  }

  const containerClass = cn(
    "w-full max-w-2xl mx-auto space-y-3",
    position === 'fixed' && "fixed top-4 right-4 z-50 max-w-md",
    position === 'top' && "mb-6",
    position === 'bottom' && "mt-6"
  )

  return (
    <div className={containerClass}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-yellow-500" />
          <h3 className="text-lg font-semibold">Continuity Alerts</h3>
          <Badge variant="outline">{activeWarnings.length}</Badge>
        </div>
        <div className="flex items-center gap-2">
          {hiddenCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowAll(!showAll)}
            >
              {showAll ? (
                <>
                  <EyeOff className="h-4 w-4 mr-1" />
                  Show Less
                </>
              ) : (
                <>
                  <Eye className="h-4 w-4 mr-1" />
                  Show All ({hiddenCount} more)
                </>
              )}
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronUp className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>

      {/* Alerts */}
      {!collapsed && (
        <div className="space-y-3">
          {visibleWarnings.map((warning) => {
            const alertState = alertStates[warning.id]
            const isExpanded = alertState?.expanded || false
            
            return (
              <Alert 
                key={warning.id} 
                variant={getAlertVariant(warning.severity)}
                className={cn(
                  "relative",
                  warning.severity === 'error' && "border-red-200 bg-red-50",
                  warning.severity === 'warning' && "border-yellow-200 bg-yellow-50",
                  warning.severity === 'info' && "border-blue-200 bg-blue-50"
                )}
              >
                <div className="flex items-start gap-3">
                  {getAlertIcon(warning.severity, warning.type)}
                  
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <AlertTitle className="text-sm font-medium">
                          {warning.title}
                        </AlertTitle>
                        <Badge 
                          variant="outline" 
                          className={cn("text-xs", getTypeColor(warning.type))}
                        >
                          {warning.type}
                        </Badge>
                        <Badge 
                          variant="outline"
                          className={cn("text-xs", getSeverityColor(warning.severity))}
                        >
                          {warning.severity}
                        </Badge>
                      </div>
                      
                      <div className="flex items-center gap-1">
                        {warning.auto_dismiss_after && (
                          <Badge variant="secondary" className="text-xs">
                            <Clock className="h-3 w-3 mr-1" />
                            {warning.auto_dismiss_after}s
                          </Badge>
                        )}
                        
                        {warning.dismissible && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDismiss(warning.id)}
                            className="h-6 w-6 p-0"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                    
                    <AlertDescription className="text-sm">
                      {isExpanded ? warning.message : `${warning.message.slice(0, 100)}${warning.message.length > 100 ? '...' : ''}`}
                    </AlertDescription>
                    
                    {warning.message.length > 100 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleExpanded(warning.id)}
                        className="h-6 text-xs p-0"
                      >
                        {isExpanded ? 'Show less' : 'Show more'}
                      </Button>
                    )}
                    
                    {warning.suggestion && isExpanded && (
                      <div className="mt-2 p-2 bg-gray-50 rounded-md">
                        <p className="text-xs text-gray-700">
                          <strong>Suggestion:</strong> {warning.suggestion}
                        </p>
                      </div>
                    )}
                    
                    {warning.action_required && (
                      <div className="flex items-center gap-2 mt-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleAction(warning.id, 'resolve')}
                          className="text-xs"
                        >
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Resolve
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleAction(warning.id, 'investigate')}
                          className="text-xs"
                        >
                          <Eye className="h-3 w-3 mr-1" />
                          Investigate
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </Alert>
            )
          })}
        </div>
      )}
    </div>
  )
} 