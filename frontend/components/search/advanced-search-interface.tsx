"use client"

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useDebounce } from '@/hooks/use-debounce'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { Textarea } from '@/components/ui/textarea'
import { 
  Search, 
  Filter, 
  Calendar as CalendarIcon, 
  Download, 
  RefreshCw,
  ChevronDown,
  ChevronUp,
  X,
  Eye,
  ExternalLink,
  Loader2,
  AlertCircle,
  FileText,
  Users,
  Clock,
  Tag,
  TrendingUp,
  Copy,
  Share,
  Settings,
  Target,
  Layers,
  BookOpen,
  MessageSquare,
  Activity,
  MapPin,
  Zap,
  Sparkles
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { format, formatDistanceToNow } from 'date-fns'
import { useToast } from '@/hooks/use-toast'

interface SearchFilter {
  id: string
  label: string
  type: 'text' | 'select' | 'multiselect' | 'daterange' | 'boolean'
  options?: Array<{ value: string; label: string; count?: number }>
  value: any
}

interface FacetedSearchFilters {
  query: string
  search_scope: 'all' | 'scenes' | 'poses' | 'characters' | 'plots'
  date_range: { start?: Date; end?: Date }
  participants: string[]
  tags: string[]
  scene_status: string[]
  pose_types: string[]
  character_names: string[]
  plot_elements: string[]
  locations: string[]
  include_archived: boolean
  content_length: { min?: number; max?: number }
  relevance_threshold: number
  sort_by: 'relevance' | 'date' | 'name' | 'activity'
  sort_order: 'asc' | 'desc'
}

interface SearchResult {
  id: string
  type: 'scene' | 'pose' | 'character' | 'plot'
  title: string
  content: string
  highlights: string[]
  metadata: Record<string, any>
  relevance_score: number
  matched_terms: string[]
  context: {
    scene_name?: string
    character_name?: string
    timestamp?: string
    location?: string
  }
}

interface SearchResultGroup {
  type: 'scene' | 'pose' | 'character' | 'plot'
  label: string
  count: number
  results: SearchResult[]
  expanded: boolean
}

interface AdvancedSearchState {
  results: SearchResultGroup[]
  loading: boolean
  error: string | null
  total_results: number
  search_time: number
  suggestions: string[]
  facet_counts: Record<string, Record<string, number>>
  has_more: boolean
}

const DEFAULT_FILTERS: FacetedSearchFilters = {
  query: '',
  search_scope: 'all',
  date_range: {},
  participants: [],
  tags: [],
  scene_status: [],
  pose_types: [],
  character_names: [],
  plot_elements: [],
  locations: [],
  include_archived: false,
  content_length: {},
  relevance_threshold: 0.3,
  sort_by: 'relevance',
  sort_order: 'desc'
}

const SEARCH_SCOPES = [
  { value: 'all', label: 'All Content', icon: Layers },
  { value: 'scenes', label: 'Scenes', icon: FileText },
  { value: 'poses', label: 'Poses', icon: MessageSquare },
  { value: 'characters', label: 'Characters', icon: Users },
  { value: 'plots', label: 'Plot Elements', icon: BookOpen }
]

export interface AdvancedSearchInterfaceProps {
  onResultSelect?: (result: SearchResult) => void
  onExport?: (results: SearchResult[], format: string) => void
  onSearchAnalytics?: (query: string, results: SearchResult[]) => void
  maxResults?: number
  enableSavedSearches?: boolean
  enableSearchAnalytics?: boolean
  className?: string
}

export function AdvancedSearchInterface({
  onResultSelect,
  onExport,
  onSearchAnalytics,
  maxResults = 100,
  enableSavedSearches = true,
  enableSearchAnalytics = true,
  className
}: AdvancedSearchInterfaceProps) {
  const [filters, setFilters] = useState<FacetedSearchFilters>(DEFAULT_FILTERS)
  const [searchState, setSearchState] = useState<AdvancedSearchState>({
    results: [],
    loading: false,
    error: null,
    total_results: 0,
    search_time: 0,
    suggestions: [],
    facet_counts: {},
    has_more: false
  })
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)
  const [selectedResults, setSelectedResults] = useState<Set<string>>(new Set())
  const [exportDialogOpen, setExportDialogOpen] = useState(false)
  const [savedSearchDialogOpen, setSavedSearchDialogOpen] = useState(false)
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(['scenes', 'poses']))

  const { toast } = useToast()
  const debouncedQuery = useDebounce(filters.query, 300)

  // Available filter options
  const [filterOptions, setFilterOptions] = useState<Record<string, Array<{ value: string; label: string; count?: number }>>>({})

  // Perform search when debounced query or other filters change
  useEffect(() => {
    if (debouncedQuery.trim() || Object.values(filters).some(v => 
      (Array.isArray(v) && v.length > 0) || 
      (typeof v === 'object' && v !== null && Object.keys(v).length > 0) ||
      (typeof v === 'boolean' && v) ||
      (typeof v === 'number' && v !== DEFAULT_FILTERS.relevance_threshold)
    )) {
      performSearch()
    }
  }, [debouncedQuery, filters.search_scope, filters.date_range, filters.participants, 
      filters.tags, filters.scene_status, filters.sort_by, filters.sort_order])

  // Load filter options on mount
  useEffect(() => {
    loadFilterOptions()
  }, [])

  const loadFilterOptions = useCallback(async () => {
    try {
      const response = await fetch('/api/search-summary/filter-options', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setFilterOptions(data.data)
        }
      }
    } catch (error) {
      console.error('Failed to load filter options:', error)
    }
  }, [])

  const performSearch = useCallback(async () => {
    const startTime = Date.now()
    setSearchState(prev => ({ ...prev, loading: true, error: null }))

    try {
      // Build search parameters
      const searchParams = {
        q: filters.query,
        search_scope: filters.search_scope,
        start_date: filters.date_range.start?.toISOString(),
        end_date: filters.date_range.end?.toISOString(),
        participants: filters.participants.join(','),
        tags: filters.tags.join(','),
        scene_status: filters.scene_status.join(','),
        pose_types: filters.pose_types.join(','),
        character_names: filters.character_names.join(','),
        plot_elements: filters.plot_elements.join(','),
        locations: filters.locations.join(','),
        include_archived: filters.include_archived,
        content_min_length: filters.content_length.min,
        content_max_length: filters.content_length.max,
        relevance_threshold: filters.relevance_threshold,
        sort: filters.sort_by,
        order: filters.sort_order,
        limit: maxResults,
        faceted: true // Enable faceted search
      }

      const params = new URLSearchParams()
      Object.entries(searchParams).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString())
        }
      })

      const response = await fetch(`/api/search-summary/search/advanced?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error('Search failed')
      }

      const data = await response.json()
      const searchTime = Date.now() - startTime

      if (data.success) {
        // Group results by type
        const groupedResults = groupSearchResults(data.data || [])
        
        setSearchState({
          results: groupedResults,
          loading: false,
          error: null,
          total_results: data.meta?.total_results || 0,
          search_time: searchTime,
          suggestions: data.meta?.suggestions || [],
          facet_counts: data.meta?.facet_counts || {},
          has_more: data.meta?.has_more || false
        })

        // Send analytics if enabled
        if (enableSearchAnalytics && onSearchAnalytics) {
          const flatResults = groupedResults.flatMap(g => g.results)
          onSearchAnalytics(filters.query, flatResults)
        }
      } else {
        throw new Error(data.message || 'Search failed')
      }
    } catch (error) {
      setSearchState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Search failed'
      }))
    }
  }, [filters, maxResults, enableSearchAnalytics, onSearchAnalytics])

  const groupSearchResults = (results: SearchResult[]): SearchResultGroup[] => {
    const groups = new Map<string, SearchResult[]>()
    
    results.forEach(result => {
      if (!groups.has(result.type)) {
        groups.set(result.type, [])
      }
      groups.get(result.type)!.push(result)
    })

    const groupLabels = {
      scene: 'Scenes',
      pose: 'Poses', 
      character: 'Characters',
      plot: 'Plot Elements'
    }

    return Array.from(groups.entries()).map(([type, results]) => ({
      type: type as 'scene' | 'pose' | 'character' | 'plot',
      label: groupLabels[type as keyof typeof groupLabels] || type,
      count: results.length,
      results,
      expanded: expandedGroups.has(type)
    }))
  }

  const toggleGroupExpansion = (groupType: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev)
      if (next.has(groupType)) {
        next.delete(groupType)
      } else {
        next.add(groupType)
      }
      return next
    })
  }

  const handleFilterChange = (key: keyof FacetedSearchFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const clearAllFilters = () => {
    setFilters(DEFAULT_FILTERS)
    setSelectedResults(new Set())
  }

  const handleResultSelect = (result: SearchResult) => {
    if (onResultSelect) {
      onResultSelect(result)
    }
  }

  const toggleResultSelection = (resultId: string) => {
    setSelectedResults(prev => {
      const next = new Set(prev)
      if (next.has(resultId)) {
        next.delete(resultId)
      } else {
        next.add(resultId)
      }
      return next
    })
  }

  const handleExport = async (format: string) => {
    if (!onExport) return

    const selectedResultsList = searchState.results
      .flatMap(group => group.results)
      .filter(result => selectedResults.has(result.id))

    if (selectedResultsList.length === 0) {
      toast({
        title: "No Results Selected",
        description: "Please select some results to export.",
        variant: "destructive"
      })
      return
    }

    try {
      await onExport(selectedResultsList, format)
      setExportDialogOpen(false)
      toast({
        title: "Export Successful",
        description: `Exported ${selectedResultsList.length} results in ${format.toUpperCase()} format.`
      })
    } catch (error) {
      toast({
        title: "Export Failed",
        description: "Failed to export search results. Please try again.",
        variant: "destructive"
      })
    }
  }

  const highlightText = (text: string, highlights: string[]) => {
    if (!highlights.length) return text

    let highlightedText = text
    highlights.forEach(highlight => {
      const regex = new RegExp(`(${highlight})`, 'gi')
      highlightedText = highlightedText.replace(regex, '<mark>$1</mark>')
    })

    return highlightedText
  }

  const getTypeIcon = (type: string) => {
    const icons = {
      scene: FileText,
      pose: MessageSquare,
      character: Users,
      plot: BookOpen
    }
    return icons[type as keyof typeof icons] || FileText
  }

  const activeFiltersCount = useMemo(() => {
    return [
      filters.participants.length,
      filters.tags.length,
      filters.scene_status.length,
      filters.pose_types.length,
      filters.character_names.length,
      filters.plot_elements.length,
      filters.locations.length,
      filters.include_archived ? 1 : 0,
      Object.keys(filters.date_range).length,
      Object.keys(filters.content_length).length,
      filters.relevance_threshold !== DEFAULT_FILTERS.relevance_threshold ? 1 : 0
    ].reduce((sum, count) => sum + count, 0)
  }, [filters])

  return (
    <div className={cn("space-y-6", className)}>
      {/* Search Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Advanced Search
            {enableSearchAnalytics && searchState.total_results > 0 && (
              <Badge variant="secondary">
                {searchState.total_results} results in {searchState.search_time}ms
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Main Search Input */}
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search scenes, poses, characters, plot elements..."
                className="pl-10"
                value={filters.query}
                onChange={(e) => handleFilterChange('query', e.target.value)}
              />
            </div>
            <Select 
              value={filters.search_scope} 
              onValueChange={(value: any) => handleFilterChange('search_scope', value)}
            >
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SEARCH_SCOPES.map(scope => (
                  <SelectItem key={scope.value} value={scope.value}>
                    <div className="flex items-center gap-2">
                      <scope.icon className="h-4 w-4" />
                      {scope.label}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button 
              variant="outline" 
              onClick={() => performSearch()}
              disabled={searchState.loading}
            >
              {searchState.loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            </Button>
          </div>

          {/* Search Suggestions */}
          {searchState.suggestions.length > 0 && (
            <div className="flex flex-wrap gap-2">
              <span className="text-sm text-muted-foreground">Suggestions:</span>
              {searchState.suggestions.map(suggestion => (
                <Button
                  key={suggestion}
                  variant="ghost"
                  size="sm"
                  className="h-6 text-xs"
                  onClick={() => handleFilterChange('query', suggestion)}
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          )}

          {/* Filter Toggle and Status */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                className="gap-2"
              >
                <Filter className="h-4 w-4" />
                Filters
                {activeFiltersCount > 0 && (
                  <Badge variant="secondary" className="ml-1">
                    {activeFiltersCount}
                  </Badge>
                )}
                {showAdvancedFilters ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </Button>
              {activeFiltersCount > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearAllFilters}
                  className="text-muted-foreground hover:text-foreground"
                >
                  Clear all
                </Button>
              )}
            </div>

            <div className="flex items-center gap-2">
              {selectedResults.size > 0 && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setExportDialogOpen(true)}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Export ({selectedResults.size})
                  </Button>
                  <Separator orientation="vertical" className="h-4" />
                </>
              )}
              {enableSavedSearches && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSavedSearchDialogOpen(true)}
                >
                  <Settings className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>

          {/* Advanced Filters Panel */}
          <Collapsible open={showAdvancedFilters}>
            <CollapsibleContent className="space-y-4 pt-4 border-t">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Date Range Filter */}
                <div className="space-y-2">
                  <Label>Date Range</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button variant="outline" className="justify-start">
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {filters.date_range.start && filters.date_range.end
                          ? `${format(filters.date_range.start, 'PPP')} - ${format(filters.date_range.end, 'PPP')}`
                          : "Select date range"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="range"
                        selected={{
                          from: filters.date_range.start,
                          to: filters.date_range.end
                        }}
                        onSelect={(range) => handleFilterChange('date_range', {
                          start: range?.from,
                          end: range?.to
                        })}
                        numberOfMonths={2}
                      />
                    </PopoverContent>
                  </Popover>
                </div>

                {/* Participants Filter */}
                <div className="space-y-2">
                  <Label>Characters</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button variant="outline" className="justify-start">
                        <Users className="mr-2 h-4 w-4" />
                        {filters.participants.length > 0 
                          ? `${filters.participants.length} selected`
                          : "Any character"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-64">
                      <Command>
                        <CommandInput placeholder="Search characters..." />
                        <CommandList>
                          <CommandEmpty>No characters found.</CommandEmpty>
                          <CommandGroup>
                            {(filterOptions.participants || []).map(option => (
                              <CommandItem
                                key={option.value}
                                onSelect={() => {
                                  const isSelected = filters.participants.includes(option.value)
                                  handleFilterChange('participants', 
                                    isSelected 
                                      ? filters.participants.filter(p => p !== option.value)
                                      : [...filters.participants, option.value]
                                  )
                                }}
                              >
                                <Checkbox 
                                  checked={filters.participants.includes(option.value)}
                                  className="mr-2"
                                />
                                {option.label}
                                {option.count && (
                                  <Badge variant="secondary" className="ml-auto">
                                    {option.count}
                                  </Badge>
                                )}
                              </CommandItem>
                            ))}
                          </CommandGroup>
                        </CommandList>
                      </Command>
                    </PopoverContent>
                  </Popover>
                </div>

                {/* Tags Filter */}
                <div className="space-y-2">
                  <Label>Tags</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button variant="outline" className="justify-start">
                        <Tag className="mr-2 h-4 w-4" />
                        {filters.tags.length > 0 
                          ? `${filters.tags.length} selected`
                          : "Any tags"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-64">
                      <Command>
                        <CommandInput placeholder="Search tags..." />
                        <CommandList>
                          <CommandEmpty>No tags found.</CommandEmpty>
                          <CommandGroup>
                            {(filterOptions.tags || []).map(option => (
                              <CommandItem
                                key={option.value}
                                onSelect={() => {
                                  const isSelected = filters.tags.includes(option.value)
                                  handleFilterChange('tags', 
                                    isSelected 
                                      ? filters.tags.filter(t => t !== option.value)
                                      : [...filters.tags, option.value]
                                  )
                                }}
                              >
                                <Checkbox 
                                  checked={filters.tags.includes(option.value)}
                                  className="mr-2"
                                />
                                {option.label}
                                {option.count && (
                                  <Badge variant="secondary" className="ml-auto">
                                    {option.count}
                                  </Badge>
                                )}
                              </CommandItem>
                            ))}
                          </CommandGroup>
                        </CommandList>
                      </Command>
                    </PopoverContent>
                  </Popover>
                </div>

                {/* Additional filters would go here... */}
              </div>

              <div className="flex items-center gap-4">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="include-archived"
                    checked={filters.include_archived}
                    onCheckedChange={(checked) => handleFilterChange('include_archived', checked)}
                  />
                  <Label htmlFor="include-archived">Include archived content</Label>
                </div>

                <div className="flex items-center gap-2 ml-auto">
                  <Label>Sort by</Label>
                  <Select 
                    value={filters.sort_by} 
                    onValueChange={(value: any) => handleFilterChange('sort_by', value)}
                  >
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="relevance">Relevance</SelectItem>
                      <SelectItem value="date">Date</SelectItem>
                      <SelectItem value="name">Name</SelectItem>
                      <SelectItem value="activity">Activity</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select 
                    value={filters.sort_order} 
                    onValueChange={(value: any) => handleFilterChange('sort_order', value)}
                  >
                    <SelectTrigger className="w-24">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="desc">Desc</SelectItem>
                      <SelectItem value="asc">Asc</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CollapsibleContent>
          </Collapsible>
        </CardContent>
      </Card>

      {/* Search Results */}
      {searchState.loading ? (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="flex items-center gap-2">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span>Searching...</span>
            </div>
          </CardContent>
        </Card>
      ) : searchState.error ? (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-6 w-6" />
              <span>{searchState.error}</span>
            </div>
          </CardContent>
        </Card>
      ) : searchState.results.length > 0 ? (
        <div className="space-y-4">
          {searchState.results.map(group => {
            const Icon = getTypeIcon(group.type)
            return (
              <Card key={group.type}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <Button
                      variant="ghost"
                      onClick={() => toggleGroupExpansion(group.type)}
                      className="flex items-center gap-2 p-0 h-auto font-semibold hover:bg-transparent"
                    >
                      <Icon className="h-5 w-5" />
                      {group.label}
                      <Badge variant="secondary">{group.count}</Badge>
                      {group.expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </Button>
                    {group.results.length > 0 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const allSelected = group.results.every(r => selectedResults.has(r.id))
                          if (allSelected) {
                            group.results.forEach(r => {
                              setSelectedResults(prev => {
                                const next = new Set(prev)
                                next.delete(r.id)
                                return next
                              })
                            })
                          } else {
                            group.results.forEach(r => {
                              setSelectedResults(prev => new Set([...prev, r.id]))
                            })
                          }
                        }}
                      >
                        Select all
                      </Button>
                    )}
                  </div>
                </CardHeader>
                {group.expanded && (
                  <CardContent className="pt-0">
                    <div className="space-y-3">
                      {group.results.map(result => (
                        <div
                          key={result.id}
                          className="flex items-start gap-3 p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                        >
                          <Checkbox
                            checked={selectedResults.has(result.id)}
                            onCheckedChange={() => toggleResultSelection(result.id)}
                            className="mt-1"
                          />
                          <div className="flex-1 space-y-2 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex-1 min-w-0">
                                <Button
                                  variant="link"
                                  onClick={() => handleResultSelect(result)}
                                  className="p-0 h-auto font-medium text-left justify-start"
                                >
                                  {result.title}
                                </Button>
                                <div className="flex items-center gap-2 mt-1">
                                  <Badge variant="outline" className="text-xs">
                                    {result.relevance_score.toFixed(2)} relevance
                                  </Badge>
                                  {result.context.scene_name && (
                                    <Badge variant="secondary" className="text-xs">
                                      {result.context.scene_name}
                                    </Badge>
                                  )}
                                  {result.context.timestamp && (
                                    <span className="text-xs text-muted-foreground">
                                      {formatDistanceToNow(new Date(result.context.timestamp))} ago
                                    </span>
                                  )}
                                </div>
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleResultSelect(result)}
                              >
                                <ExternalLink className="h-4 w-4" />
                              </Button>
                            </div>
                            <div 
                              className="text-sm text-muted-foreground line-clamp-2"
                              dangerouslySetInnerHTML={{ 
                                __html: highlightText(result.content, result.highlights) 
                              }}
                            />
                            {result.matched_terms.length > 0 && (
                              <div className="flex flex-wrap gap-1">
                                {result.matched_terms.map(term => (
                                  <Badge key={term} variant="outline" className="text-xs">
                                    {term}
                                  </Badge>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                )}
              </Card>
            )
          })}
        </div>
      ) : filters.query.trim() || activeFiltersCount > 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Search className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No results found</h3>
            <p className="text-muted-foreground text-center">
              Try adjusting your search terms or filters to find what you're looking for.
            </p>
          </CardContent>
        </Card>
      ) : null}

      {/* Export Dialog */}
      <Dialog open={exportDialogOpen} onOpenChange={setExportDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Export Search Results</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Export {selectedResults.size} selected results in your preferred format.
            </p>
            <div className="grid grid-cols-3 gap-2">
              <Button onClick={() => handleExport('json')} className="flex-col gap-1 h-16">
                <FileText className="h-6 w-6" />
                JSON
              </Button>
              <Button onClick={() => handleExport('csv')} className="flex-col gap-1 h-16">
                <FileText className="h-6 w-6" />
                CSV
              </Button>
              <Button onClick={() => handleExport('txt')} className="flex-col gap-1 h-16">
                <FileText className="h-6 w-6" />
                Text
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
} 