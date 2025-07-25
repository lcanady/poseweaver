"use client"

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useDebounce } from '../../hooks/use-debounce'
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
  Share
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { format } from 'date-fns'
import type { 
  SceneSearchFilters, 
  SceneSearchResult, 
  SceneSearchProps, 
  SceneExportOptions 
} from '@/types/scene'

interface SearchState {
  results: SceneSearchResult[]
  loading: boolean
  error: string | null
  hasMore: boolean
  total: number
}

interface AdvancedFilters {
  tags: string[]
  participants: string[]
  wordCountMin?: number
  wordCountMax?: number
  poseCountMin?: number
  poseCountMax?: number
  sentiment?: string
  plotSignificance?: number
}

const DEFAULT_FILTERS: SceneSearchFilters = {
  query: '',
  sort_by: 'relevance',
  sort_order: 'desc',
  limit: 20,
  skip: 0
}

export function SceneSearchInterface({
  initialFilters = DEFAULT_FILTERS,
  onSearchResults,
  onFilterChange,
  showAdvancedFilters = true,
  showExportOptions = true,
  placeholder = "Search scenes, poses, characters...",
  maxResults = 100
}: SceneSearchProps) {
  const [filters, setFilters] = useState<SceneSearchFilters>(initialFilters)
  const [advancedFilters, setAdvancedFilters] = useState<AdvancedFilters>({
    tags: [],
    participants: []
  })
  const [searchState, setSearchState] = useState<SearchState>({
    results: [],
    loading: false,
    error: null,
    hasMore: false,
    total: 0
  })
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [selectedResults, setSelectedResults] = useState<Set<string>>(new Set())
  const [exportDialogOpen, setExportDialogOpen] = useState(false)
  const [searchMode, setSearchMode] = useState<'scenes' | 'poses' | 'characters'>('scenes')
  const [dateRange, setDateRange] = useState<{ start?: Date; end?: Date }>({})

  // Debounce search query to avoid excessive API calls
  const debouncedQuery = useDebounce(filters.query, 300)

  // Available tags and participants for filter suggestions
  const [availableTags, setAvailableTags] = useState<string[]>([])
  const [availableParticipants, setAvailableParticipants] = useState<string[]>([])

  // Perform search when filters change
  useEffect(() => {
    performSearch()
  }, [debouncedQuery, filters.sort_by, filters.sort_order, filters.active, filters.status, searchMode])

  // Load filter suggestions
  useEffect(() => {
    loadFilterSuggestions()
  }, [])

  const loadFilterSuggestions = useCallback(async () => {
    try {
      // TODO: Replace with actual API calls
      const [tagsResponse, participantsResponse] = await Promise.all([
        fetch('/api/search-summary/suggestions/tags', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch('/api/search-summary/suggestions/participants', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        })
      ])

      if (tagsResponse.ok) {
        const tagsData = await tagsResponse.json()
        setAvailableTags(tagsData.data || [])
      }

      if (participantsResponse.ok) {
        const participantsData = await participantsResponse.json()
        setAvailableParticipants(participantsData.data || [])
      }
    } catch (error) {
      console.error('Failed to load filter suggestions:', error)
    }
  }, [])

  const performSearch = useCallback(async () => {
    setSearchState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const searchFilters = {
        ...filters,
        ...advancedFilters,
        start_date: dateRange.start?.toISOString(),
        end_date: dateRange.end?.toISOString()
      }

      let endpoint = '/api/search-summary/search/'
      switch (searchMode) {
        case 'scenes':
          endpoint += 'scenes'
          break
        case 'poses':
          endpoint += 'poses'
          break
        case 'characters':
          endpoint += 'characters'
          break
      }

      const params = new URLSearchParams()
      Object.entries(searchFilters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          if (Array.isArray(value)) {
            params.append(key, value.join(','))
          } else {
            params.append(key, value.toString())
          }
        }
      })

      const response = await fetch(`${endpoint}?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error('Search failed')
      }

      const data = await response.json()
      
      if (data.success) {
        const results = data.data || []
        setSearchState({
          results,
          loading: false,
          error: null,
          hasMore: results.length === filters.limit,
          total: data.meta?.total_results || results.length
        })

        // Notify parent component
        if (onSearchResults) {
          onSearchResults(results)
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
  }, [filters, advancedFilters, dateRange, searchMode, onSearchResults])

  const handleFilterChange = useCallback((newFilters: Partial<SceneSearchFilters>) => {
    const updatedFilters = { ...filters, ...newFilters, skip: 0 }
    setFilters(updatedFilters)
    
    if (onFilterChange) {
      onFilterChange(updatedFilters)
    }
  }, [filters, onFilterChange])

  const handleAdvancedFilterChange = useCallback((newFilters: Partial<AdvancedFilters>) => {
    setAdvancedFilters(prev => ({ ...prev, ...newFilters }))
  }, [])

  const loadMore = useCallback(async () => {
    if (!searchState.hasMore || searchState.loading) return

    const newFilters = { ...filters, skip: searchState.results.length }
    setFilters(newFilters)
  }, [filters, searchState.hasMore, searchState.loading, searchState.results.length])

  const clearFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS)
    setAdvancedFilters({ tags: [], participants: [] })
    setDateRange({})
    setSelectedResults(new Set())
  }, [])

  const toggleResultSelection = useCallback((resultId: string) => {
    setSelectedResults(prev => {
      const newSet = new Set(prev)
      if (newSet.has(resultId)) {
        newSet.delete(resultId)
      } else {
        newSet.add(resultId)
      }
      return newSet
    })
  }, [])

  const selectAllResults = useCallback(() => {
    setSelectedResults(new Set(searchState.results.map(r => r.item_id)))
  }, [searchState.results])

  const clearSelection = useCallback(() => {
    setSelectedResults(new Set())
  }, [])

  const exportResults = useCallback(async (options: SceneExportOptions) => {
    try {
      const selectedIds = Array.from(selectedResults)
      const resultsToExport = selectedIds.length > 0 
        ? searchState.results.filter(r => selectedIds.includes(r.item_id))
        : searchState.results

      const exportData = {
        search_type: searchMode,
        search_params: {
          ...filters,
          ...advancedFilters,
          start_date: dateRange.start?.toISOString(),
          end_date: dateRange.end?.toISOString()
        },
        ...options
      }

      const response = await fetch('/api/search-summary/export/search-results', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(exportData)
      })

      if (!response.ok) {
        throw new Error('Export failed')
      }

      // Handle different response types
      if (options.format === 'json') {
        const data = await response.json()
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `search-results-${Date.now()}.json`
        a.click()
        URL.revokeObjectURL(url)
      } else {
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `search-results-${Date.now()}.${options.format}`
        a.click()
        URL.revokeObjectURL(url)
      }

      setExportDialogOpen(false)
    } catch (error) {
      console.error('Export failed:', error)
    }
  }, [selectedResults, searchState.results, searchMode, filters, advancedFilters, dateRange])

  const getResultIcon = (type: string) => {
    switch (type) {
      case 'scene':
        return <FileText className="h-4 w-4" />
      case 'pose':
        return <Users className="h-4 w-4" />
      case 'character':
        return <Users className="h-4 w-4" />
      default:
        return <FileText className="h-4 w-4" />
    }
  }

  const formatTimestamp = (timestamp: string) => {
    return format(new Date(timestamp), 'MMM d, yyyy h:mm a')
  }

  const getRelevanceColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-100 text-green-800'
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-800'
    if (score >= 0.4) return 'bg-orange-100 text-orange-800'
    return 'bg-red-100 text-red-800'
  }

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Scene Search
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search Input */}
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={placeholder}
                className="pl-10"
                value={filters.query}
                onChange={(e) => handleFilterChange({ query: e.target.value })}
              />
            </div>
            <Select 
              value={searchMode} 
              onValueChange={(value: any) => setSearchMode(value)}
            >
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="scenes">Scenes</SelectItem>
                <SelectItem value="poses">Poses</SelectItem>
                <SelectItem value="characters">Characters</SelectItem>
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

          {/* Basic Filters */}
          <div className="flex flex-wrap gap-2">
            <Select 
              value={filters.sort_by} 
              onValueChange={(value: any) => handleFilterChange({ sort_by: value })}
            >
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="relevance">Relevance</SelectItem>
                <SelectItem value="created_at">Created</SelectItem>
                <SelectItem value="updated_at">Updated</SelectItem>
                <SelectItem value="name">Name</SelectItem>
              </SelectContent>
            </Select>

            <Select 
              value={filters.sort_order} 
              onValueChange={(value: any) => handleFilterChange({ sort_order: value })}
            >
              <SelectTrigger className="w-28">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="desc">Desc</SelectItem>
                <SelectItem value="asc">Asc</SelectItem>
              </SelectContent>
            </Select>

            {searchMode === 'scenes' && (
                          <Select 
              value={filters.status || 'all'} 
              onValueChange={(value) => handleFilterChange({ status: value === 'all' ? undefined : value as any })}
            >
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="archived">Archived</SelectItem>
              </SelectContent>
            </Select>
            )}

            {showAdvancedFilters && (
              <Button
                variant="outline"
                onClick={() => setShowAdvanced(!showAdvanced)}
              >
                <Filter className="h-4 w-4 mr-2" />
                Advanced
                {showAdvanced ? <ChevronUp className="h-4 w-4 ml-2" /> : <ChevronDown className="h-4 w-4 ml-2" />}
              </Button>
            )}

            <Button variant="outline" onClick={clearFilters}>
              <X className="h-4 w-4 mr-2" />
              Clear
            </Button>
          </div>

          {/* Advanced Filters */}
          {showAdvancedFilters && (
            <Collapsible open={showAdvanced} onOpenChange={setShowAdvanced}>
              <CollapsibleContent className="space-y-4">
                <Separator />
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {/* Date Range */}
                  <div className="space-y-2">
                    <Label>Date Range</Label>
                    <div className="flex gap-2">
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button variant="outline" className="flex-1">
                            <CalendarIcon className="h-4 w-4 mr-2" />
                            {dateRange.start ? format(dateRange.start, 'MMM d') : 'Start'}
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0">
                          <Calendar
                            mode="single"
                            selected={dateRange.start}
                            onSelect={(date) => setDateRange(prev => ({ ...prev, start: date }))}
                            initialFocus
                          />
                        </PopoverContent>
                      </Popover>
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button variant="outline" className="flex-1">
                            <CalendarIcon className="h-4 w-4 mr-2" />
                            {dateRange.end ? format(dateRange.end, 'MMM d') : 'End'}
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0">
                          <Calendar
                            mode="single"
                            selected={dateRange.end}
                            onSelect={(date) => setDateRange(prev => ({ ...prev, end: date }))}
                            initialFocus
                          />
                        </PopoverContent>
                      </Popover>
                    </div>
                  </div>

                  {/* Tags */}
                  <div className="space-y-2">
                    <Label>Tags</Label>
                    <div className="flex flex-wrap gap-1">
                      {availableTags.slice(0, 5).map(tag => (
                        <Badge
                          key={tag}
                          variant={advancedFilters.tags.includes(tag) ? 'default' : 'outline'}
                          className="cursor-pointer"
                          onClick={() => {
                            const newTags = advancedFilters.tags.includes(tag)
                              ? advancedFilters.tags.filter(t => t !== tag)
                              : [...advancedFilters.tags, tag]
                            handleAdvancedFilterChange({ tags: newTags })
                          }}
                        >
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Participants */}
                  <div className="space-y-2">
                    <Label>Participants</Label>
                    <div className="flex flex-wrap gap-1">
                      {availableParticipants.slice(0, 5).map(participant => (
                        <Badge
                          key={participant}
                          variant={advancedFilters.participants.includes(participant) ? 'default' : 'outline'}
                          className="cursor-pointer"
                          onClick={() => {
                            const newParticipants = advancedFilters.participants.includes(participant)
                              ? advancedFilters.participants.filter(p => p !== participant)
                              : [...advancedFilters.participants, participant]
                            handleAdvancedFilterChange({ participants: newParticipants })
                          }}
                        >
                          {participant}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </CollapsibleContent>
            </Collapsible>
          )}
        </CardContent>
      </Card>

      {/* Search Results */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Search Results
              {searchState.total > 0 && (
                <Badge variant="secondary">{searchState.total}</Badge>
              )}
            </CardTitle>
            <div className="flex items-center gap-2">
              {selectedResults.size > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">
                    {selectedResults.size} selected
                  </span>
                  <Button variant="outline" size="sm" onClick={clearSelection}>
                    Clear
                  </Button>
                </div>
              )}
              {showExportOptions && searchState.results.length > 0 && (
                <Dialog open={exportDialogOpen} onOpenChange={setExportDialogOpen}>
                  <DialogTrigger asChild>
                    <Button variant="outline" size="sm">
                      <Download className="h-4 w-4 mr-2" />
                      Export
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Export Search Results</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div className="flex gap-2">
                        <Button onClick={() => exportResults({ format: 'json', include_poses: true, include_metadata: true, include_summaries: false, include_analytics: false })}>
                          JSON
                        </Button>
                        <Button onClick={() => exportResults({ format: 'csv', include_poses: true, include_metadata: true, include_summaries: false, include_analytics: false })}>
                          CSV
                        </Button>
                        <Button onClick={() => exportResults({ format: 'txt', include_poses: true, include_metadata: true, include_summaries: false, include_analytics: false })}>
                          TXT
                        </Button>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {selectedResults.size > 0 
                          ? `Exporting ${selectedResults.size} selected results`
                          : `Exporting all ${searchState.results.length} results`}
                      </p>
                    </div>
                  </DialogContent>
                </Dialog>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {searchState.loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : searchState.error ? (
            <div className="flex items-center justify-center py-8">
              <AlertCircle className="h-6 w-6 text-red-500 mr-2" />
              <span className="text-red-500">{searchState.error}</span>
            </div>
          ) : searchState.results.length === 0 ? (
            <div className="text-center py-8">
              <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No results found</h3>
              <p className="text-muted-foreground">
                Try adjusting your search terms or filters.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Bulk Actions */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Checkbox
                    checked={selectedResults.size === searchState.results.length}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        selectAllResults()
                      } else {
                        clearSelection()
                      }
                    }}
                  />
                  <span className="text-sm text-muted-foreground">
                    Select all
                  </span>
                </div>
                <span className="text-sm text-muted-foreground">
                  Showing {searchState.results.length} of {searchState.total} results
                </span>
              </div>

              {/* Results List */}
              <div className="space-y-3">
                {searchState.results.map((result, index) => (
                  <div
                    key={result.item_id}
                    className={cn(
                      "flex items-start gap-3 p-4 border rounded-lg hover:bg-accent/50 transition-colors",
                      selectedResults.has(result.item_id) && "bg-accent/50 border-primary"
                    )}
                  >
                    <Checkbox
                      checked={selectedResults.has(result.item_id)}
                      onCheckedChange={() => toggleResultSelection(result.item_id)}
                    />
                    
                    <div className="flex items-center gap-2 text-muted-foreground">
                      {getResultIcon(result.item_type)}
                      <Badge variant="outline" className="text-xs">
                        {result.item_type}
                      </Badge>
                    </div>

                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium">
                          {result.metadata.scene_name || result.metadata.character_name || result.item_id}
                        </h4>
                        <Badge variant="outline" className={getRelevanceColor(result.relevance_score)}>
                          {(result.relevance_score * 100).toFixed(0)}%
                        </Badge>
                      </div>
                      
                      <p className="text-sm text-muted-foreground">
                        {result.content_preview}
                      </p>
                      
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatTimestamp(result.timestamp)}
                        </span>
                        {result.metadata.character_name && (
                                                  <span className="flex items-center gap-1">
                          <Users className="h-3 w-3" />
                          {result.metadata.character_name}
                        </span>
                        )}
                        {result.metadata.word_count && (
                          <span>{result.metadata.word_count} words</span>
                        )}
                        {result.metadata.tags && result.metadata.tags.length > 0 && (
                          <div className="flex gap-1">
                            {result.metadata.tags.slice(0, 3).map(tag => (
                              <Badge key={tag} variant="outline" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          navigator.clipboard.writeText(result.content_preview)
                        }}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          // TODO: Navigate to full view
                        }}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          // TODO: Open in new tab
                        }}
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Load More */}
              {searchState.hasMore && (
                <div className="flex justify-center">
                  <Button
                    variant="outline"
                    onClick={loadMore}
                    disabled={searchState.loading}
                  >
                    {searchState.loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                    Load More
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
} 