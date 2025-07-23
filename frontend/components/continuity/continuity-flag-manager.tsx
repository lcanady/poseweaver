"use client"

import { useState, useEffect, useCallback, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { 
  Flag, 
  Filter, 
  CheckCircle, 
  X, 
  Eye, 
  Search,
  ArrowUpDown,
  ChevronDown,
  ChevronUp,
  Calendar,
  User,
  AlertTriangle,
  Clock,
  CheckSquare,
  Square,
  Trash2,
  Archive,
  ExternalLink,
  MessageSquare,
  Loader2
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import { format } from 'date-fns'

import type { 
  ContinuityFlagManagerProps, 
  ContinuityFlag, 
  ContinuityFlagFilters 
} from '@/types/continuity'

interface FlagManagerState {
  searchQuery: string
  filters: ContinuityFlagFilters
  sortBy: 'created_at' | 'severity' | 'flag_type' | 'confidence_score'
  sortOrder: 'asc' | 'desc'
  selectedFlags: Set<string>
  showFilters: boolean
  showResolutionDialog: boolean
  resolvingFlagId: string | null
  bulkAction: string | null
  currentPage: number
  resolutionText: string
  loading: boolean
}

const FLAG_TYPE_LABELS = {
  character_consistency: 'Character Consistency',
  environmental_contradiction: 'Environmental Contradiction',
  timeline_error: 'Timeline Error',
  plot_hole: 'Plot Hole',
  relationship_inconsistency: 'Relationship Inconsistency'
}

const SEVERITY_COLORS = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  low: 'bg-blue-100 text-blue-800 border-blue-200'
}

const TYPE_COLORS = {
  character_consistency: 'bg-blue-100 text-blue-800',
  environmental_contradiction: 'bg-green-100 text-green-800',
  timeline_error: 'bg-purple-100 text-purple-800',
  plot_hole: 'bg-red-100 text-red-800',
  relationship_inconsistency: 'bg-yellow-100 text-yellow-800'
}

export function ContinuityFlagManager({
  scene_id,
  flags,
  onResolve,
  onFilter,
  onSort,
  showResolved = false,
  showFilters = true,
  showBulkActions = true,
  paginate = true,
  pageSize = 20
}: ContinuityFlagManagerProps) {
  const [state, setState] = useState<FlagManagerState>({
    searchQuery: '',
    filters: {
      flag_type: [],
      severity: [],
      resolved: showResolved ? undefined : false
    },
    sortBy: 'created_at',
    sortOrder: 'desc',
    selectedFlags: new Set(),
    showFilters: false,
    showResolutionDialog: false,
    resolvingFlagId: null,
    bulkAction: null,
    currentPage: 0,
    resolutionText: '',
    loading: false
  })

  const { toast } = useToast()

  // Filter and sort flags
  const filteredFlags = useMemo(() => {
    let filtered = [...flags]

    // Apply search filter
    if (state.searchQuery) {
      const query = state.searchQuery.toLowerCase()
      filtered = filtered.filter(flag =>
        flag.title.toLowerCase().includes(query) ||
        flag.description.toLowerCase().includes(query) ||
        flag.character_name?.toLowerCase().includes(query)
      )
    }

    // Apply type filter
    if (state.filters.flag_type && state.filters.flag_type.length > 0) {
      filtered = filtered.filter(flag => 
        state.filters.flag_type!.includes(flag.flag_type)
      )
    }

    // Apply severity filter
    if (state.filters.severity && state.filters.severity.length > 0) {
      filtered = filtered.filter(flag => 
        state.filters.severity!.includes(flag.severity)
      )
    }

    // Apply resolved filter
    if (state.filters.resolved !== undefined) {
      filtered = filtered.filter(flag => flag.resolved === state.filters.resolved)
    }

    // Apply date range filter
    if (state.filters.date_range) {
      filtered = filtered.filter(flag => {
        const flagDate = new Date(flag.created_at)
        const startDate = new Date(state.filters.date_range!.start)
        const endDate = new Date(state.filters.date_range!.end)
        return flagDate >= startDate && flagDate <= endDate
      })
    }

    // Apply character filter
    if (state.filters.character_id) {
      filtered = filtered.filter(flag => 
        flag.character_id === state.filters.character_id
      )
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aVal: any, bVal: any
      
      switch (state.sortBy) {
        case 'created_at':
          aVal = new Date(a.created_at).getTime()
          bVal = new Date(b.created_at).getTime()
          break
        case 'severity':
          const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 }
          aVal = severityOrder[a.severity as keyof typeof severityOrder]
          bVal = severityOrder[b.severity as keyof typeof severityOrder]
          break
        case 'flag_type':
          aVal = a.flag_type
          bVal = b.flag_type
          break
        case 'confidence_score':
          aVal = a.confidence_score
          bVal = b.confidence_score
          break
        default:
          aVal = a.created_at
          bVal = b.created_at
      }

      if (state.sortOrder === 'desc') {
        return aVal > bVal ? -1 : aVal < bVal ? 1 : 0
      } else {
        return aVal < bVal ? -1 : aVal > bVal ? 1 : 0
      }
    })

    return filtered
  }, [flags, state.searchQuery, state.filters, state.sortBy, state.sortOrder])

  // Paginate results
  const totalPages = Math.ceil(filteredFlags.length / pageSize)
  const paginatedFlags = paginate 
    ? filteredFlags.slice(state.currentPage * pageSize, (state.currentPage + 1) * pageSize)
    : filteredFlags

  // Handle search
  const handleSearch = useCallback((query: string) => {
    setState(prev => ({ ...prev, searchQuery: query, currentPage: 0 }))
  }, [])

  // Handle filter change
  const handleFilterChange = useCallback((newFilters: Partial<ContinuityFlagFilters>) => {
    const updatedFilters = { ...state.filters, ...newFilters }
    setState(prev => ({ ...prev, filters: updatedFilters, currentPage: 0 }))
    onFilter?.(updatedFilters)
  }, [state.filters, onFilter])

  // Handle sort change
  const handleSortChange = useCallback((sortBy: string, sortOrder: 'asc' | 'desc') => {
    setState(prev => ({ ...prev, sortBy: sortBy as any, sortOrder, currentPage: 0 }))
    onSort?.(sortBy, sortOrder)
  }, [onSort])

  // Handle flag selection
  const handleFlagSelect = useCallback((flagId: string, selected: boolean) => {
    setState(prev => {
      const newSelected = new Set(prev.selectedFlags)
      if (selected) {
        newSelected.add(flagId)
      } else {
        newSelected.delete(flagId)
      }
      return { ...prev, selectedFlags: newSelected }
    })
  }, [])

  // Handle select all
  const handleSelectAll = useCallback((selected: boolean) => {
    setState(prev => ({
      ...prev,
      selectedFlags: selected ? new Set(paginatedFlags.map(f => f.id)) : new Set()
    }))
  }, [paginatedFlags])

  // Handle flag resolution
  const handleResolveFlag = useCallback(async (flagId: string, resolution: string) => {
    setState(prev => ({ ...prev, loading: true }))
    
    try {
      await onResolve?.(flagId, resolution)
      
      setState(prev => ({
        ...prev,
        showResolutionDialog: false,
        resolvingFlagId: null,
        resolutionText: '',
        selectedFlags: new Set([...prev.selectedFlags].filter(id => id !== flagId)),
        loading: false
      }))
      
      toast({
        title: "Flag Resolved",
        description: "The continuity flag has been resolved successfully.",
        variant: "default",
      })
    } catch (error) {
      setState(prev => ({ ...prev, loading: false }))
      toast({
        title: "Error",
        description: "Failed to resolve the continuity flag. Please try again.",
        variant: "destructive",
      })
    }
  }, [onResolve, toast])

  // Handle bulk actions
  const handleBulkAction = useCallback(async (action: string) => {
    if (state.selectedFlags.size === 0) return
    
    setState(prev => ({ ...prev, loading: true, bulkAction: action }))
    
    try {
      if (action === 'resolve') {
        // Resolve all selected flags
        for (const flagId of state.selectedFlags) {
          await onResolve?.(flagId, 'Bulk resolved')
        }
        
        toast({
          title: "Bulk Action Complete",
          description: `${state.selectedFlags.size} flags have been resolved.`,
          variant: "default",
        })
      }
      
      setState(prev => ({
        ...prev,
        selectedFlags: new Set(),
        loading: false,
        bulkAction: null
      }))
    } catch (error) {
      setState(prev => ({ ...prev, loading: false, bulkAction: null }))
      toast({
        title: "Error",
        description: "Bulk action failed. Please try again.",
        variant: "destructive",
      })
    }
  }, [state.selectedFlags, onResolve, toast])

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      case 'high':
        return <AlertTriangle className="h-4 w-4 text-orange-500" />
      case 'medium':
        return <Flag className="h-4 w-4 text-yellow-500" />
      case 'low':
        return <Flag className="h-4 w-4 text-blue-500" />
      default:
        return <Flag className="h-4 w-4 text-gray-500" />
    }
  }

  const allSelected = paginatedFlags.length > 0 && paginatedFlags.every(flag => state.selectedFlags.has(flag.id))
  const someSelected = paginatedFlags.some(flag => state.selectedFlags.has(flag.id))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Flag className="h-6 w-6 text-primary" />
          <h2 className="text-xl font-semibold">Continuity Flags</h2>
          <Badge variant="outline">{filteredFlags.length}</Badge>
        </div>
        
        {showBulkActions && state.selectedFlags.size > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              {state.selectedFlags.size} selected
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleBulkAction('resolve')}
              disabled={state.loading}
            >
              {state.loading && state.bulkAction === 'resolve' ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <CheckCircle className="h-4 w-4 mr-2" />
              )}
              Resolve Selected
            </Button>
          </div>
        )}
      </div>

      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 flex-1">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search flags..."
                  value={state.searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="pl-10"
                />
              </div>
              
              <Select
                value={`${state.sortBy}-${state.sortOrder}`}
                onValueChange={(value) => {
                  const [sortBy, sortOrder] = value.split('-')
                  handleSortChange(sortBy, sortOrder as 'asc' | 'desc')
                }}
              >
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="created_at-desc">Newest First</SelectItem>
                  <SelectItem value="created_at-asc">Oldest First</SelectItem>
                  <SelectItem value="severity-desc">Highest Severity</SelectItem>
                  <SelectItem value="severity-asc">Lowest Severity</SelectItem>
                  <SelectItem value="confidence_score-desc">Highest Confidence</SelectItem>
                  <SelectItem value="confidence_score-asc">Lowest Confidence</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            {showFilters && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setState(prev => ({ ...prev, showFilters: !prev.showFilters }))}
              >
                <Filter className="h-4 w-4 mr-2" />
                Filters
                {state.showFilters ? (
                  <ChevronUp className="h-4 w-4 ml-2" />
                ) : (
                  <ChevronDown className="h-4 w-4 ml-2" />
                )}
              </Button>
            )}
          </div>
        </CardHeader>
        
        {/* Filters Panel */}
        {state.showFilters && (
          <CardContent className="border-t">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label className="text-sm font-medium mb-2 block">Flag Type</Label>
                <div className="space-y-2">
                  {Object.entries(FLAG_TYPE_LABELS).map(([type, label]) => (
                    <div key={type} className="flex items-center space-x-2">
                      <Checkbox
                        id={type}
                        checked={state.filters.flag_type?.includes(type as any) || false}
                        onCheckedChange={(checked) => {
                          const currentTypes = state.filters.flag_type || []
                          const newTypes = checked
                            ? [...currentTypes, type as any]
                            : currentTypes.filter(t => t !== type)
                          handleFilterChange({ flag_type: newTypes })
                        }}
                      />
                      <Label htmlFor={type} className="text-sm font-normal">
                        {label}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <Label className="text-sm font-medium mb-2 block">Severity</Label>
                <div className="space-y-2">
                  {['critical', 'high', 'medium', 'low'].map((severity) => (
                    <div key={severity} className="flex items-center space-x-2">
                      <Checkbox
                        id={severity}
                        checked={state.filters.severity?.includes(severity as any) || false}
                        onCheckedChange={(checked) => {
                          const currentSeverities = state.filters.severity || []
                          const newSeverities = checked
                            ? [...currentSeverities, severity as any]
                            : currentSeverities.filter(s => s !== severity)
                          handleFilterChange({ severity: newSeverities })
                        }}
                      />
                      <Label htmlFor={severity} className="text-sm font-normal capitalize">
                        {severity}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <Label className="text-sm font-medium mb-2 block">Status</Label>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="unresolved"
                      checked={state.filters.resolved === false}
                      onCheckedChange={(checked) => {
                        handleFilterChange({ resolved: checked ? false : undefined })
                      }}
                    />
                    <Label htmlFor="unresolved" className="text-sm font-normal">
                      Unresolved
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="resolved"
                      checked={state.filters.resolved === true}
                      onCheckedChange={(checked) => {
                        handleFilterChange({ resolved: checked ? true : undefined })
                      }}
                    />
                    <Label htmlFor="resolved" className="text-sm font-normal">
                      Resolved
                    </Label>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Bulk Actions Bar */}
      {showBulkActions && (
        <Card>
          <CardContent className="py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Checkbox
                  checked={allSelected}
                  ref={(ref) => {
                    if (ref) {
                      ref.indeterminate = someSelected && !allSelected
                    }
                  }}
                  onCheckedChange={handleSelectAll}
                />
                <span className="text-sm font-medium">
                  Select All ({paginatedFlags.length})
                </span>
              </div>
              
              {state.selectedFlags.size > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">
                    {state.selectedFlags.size} selected
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleBulkAction('resolve')}
                    disabled={state.loading}
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Resolve
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Flags List */}
      <div className="space-y-4">
        {paginatedFlags.map((flag) => (
          <Card key={flag.id} className={cn(
            "transition-all duration-200",
            state.selectedFlags.has(flag.id) && "ring-2 ring-primary/50",
            flag.resolved && "opacity-75"
          )}>
            <CardContent className="p-4">
              <div className="flex items-start gap-4">
                {showBulkActions && (
                  <Checkbox
                    checked={state.selectedFlags.has(flag.id)}
                    onCheckedChange={(checked) => handleFlagSelect(flag.id, checked as boolean)}
                    className="mt-1"
                  />
                )}
                
                <div className="flex-1 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getSeverityIcon(flag.severity)}
                      <h3 className="font-medium">{flag.title}</h3>
                      <Badge 
                        variant="outline" 
                        className={cn("text-xs", SEVERITY_COLORS[flag.severity as keyof typeof SEVERITY_COLORS])}
                      >
                        {flag.severity}
                      </Badge>
                      <Badge 
                        variant="outline" 
                        className={cn("text-xs", TYPE_COLORS[flag.flag_type as keyof typeof TYPE_COLORS])}
                      >
                        {FLAG_TYPE_LABELS[flag.flag_type as keyof typeof FLAG_TYPE_LABELS]}
                      </Badge>
                      {flag.resolved && (
                        <Badge variant="outline" className="text-xs bg-green-100 text-green-800">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Resolved
                        </Badge>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground">
                        {flag.confidence_score}% confidence
                      </span>
                      {!flag.resolved && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setState(prev => ({ 
                            ...prev, 
                            showResolutionDialog: true, 
                            resolvingFlagId: flag.id 
                          }))}
                        >
                          <CheckCircle className="h-4 w-4 mr-1" />
                          Resolve
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  <p className="text-sm text-muted-foreground">
                    {flag.description}
                  </p>
                  
                  {flag.suggestion && (
                    <div className="p-2 bg-blue-50 rounded-md border border-blue-200">
                      <p className="text-sm text-blue-800">
                        <strong>Suggestion:</strong> {flag.suggestion}
                      </p>
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {format(new Date(flag.created_at), 'MMM d, yyyy h:mm a')}
                      </div>
                      {flag.character_name && (
                        <div className="flex items-center gap-1">
                          <User className="h-3 w-3" />
                          {flag.character_name}
                        </div>
                      )}
                    </div>
                    
                    {flag.resolved && flag.resolved_at && (
                      <div className="flex items-center gap-1">
                        <CheckCircle className="h-3 w-3 text-green-500" />
                        Resolved {format(new Date(flag.resolved_at), 'MMM d, yyyy')}
                      </div>
                    )}
                  </div>
                  
                  {flag.resolved && flag.resolution_notes && (
                    <div className="p-2 bg-green-50 rounded-md border border-green-200">
                      <p className="text-sm text-green-800">
                        <strong>Resolution:</strong> {flag.resolution_notes}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        
        {filteredFlags.length === 0 && (
          <Card>
            <CardContent className="p-8 text-center">
              <Flag className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Flags Found</h3>
              <p className="text-muted-foreground">
                {flags.length === 0 
                  ? "No continuity flags have been created yet."
                  : "No flags match your current filters. Try adjusting your search criteria."
                }
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Pagination */}
      {paginate && totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setState(prev => ({ ...prev, currentPage: Math.max(0, prev.currentPage - 1) }))}
            disabled={state.currentPage === 0}
          >
            Previous
          </Button>
          
          <div className="flex items-center gap-1">
            {Array.from({ length: totalPages }, (_, i) => (
              <Button
                key={i}
                variant={state.currentPage === i ? "default" : "outline"}
                size="sm"
                onClick={() => setState(prev => ({ ...prev, currentPage: i }))}
                className="w-8 h-8 p-0"
              >
                {i + 1}
              </Button>
            ))}
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setState(prev => ({ ...prev, currentPage: Math.min(totalPages - 1, prev.currentPage + 1) }))}
            disabled={state.currentPage === totalPages - 1}
          >
            Next
          </Button>
        </div>
      )}

      {/* Resolution Dialog */}
      <Dialog open={state.showResolutionDialog} onOpenChange={(open) => 
        setState(prev => ({ 
          ...prev, 
          showResolutionDialog: open, 
          resolvingFlagId: open ? prev.resolvingFlagId : null,
          resolutionText: open ? prev.resolutionText : ''
        }))
      }>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Resolve Continuity Flag</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="resolution">Resolution Notes</Label>
              <Textarea
                id="resolution"
                placeholder="Explain how this flag was resolved..."
                value={state.resolutionText}
                onChange={(e) => setState(prev => ({ ...prev, resolutionText: e.target.value }))}
                className="mt-1"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setState(prev => ({ ...prev, showResolutionDialog: false }))}>
              Cancel
            </Button>
            <Button 
              onClick={() => {
                if (state.resolvingFlagId) {
                  handleResolveFlag(state.resolvingFlagId, state.resolutionText || 'Resolved')
                }
              }}
              disabled={state.loading}
            >
              {state.loading ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <CheckCircle className="h-4 w-4 mr-2" />
              )}
              Resolve Flag
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
} 