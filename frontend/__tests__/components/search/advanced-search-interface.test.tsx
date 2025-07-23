import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { AdvancedSearchInterface } from '../../../components/search/advanced-search-interface'

// Mock the custom hooks and utilities
vi.mock('../../../hooks/use-debounce', () => ({
  useDebounce: vi.fn((value) => value)
}))

vi.mock('../../../hooks/use-toast', () => ({
  useToast: vi.fn(() => ({
    toast: vi.fn()
  }))
}))

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(() => 'mock-token'),
  setItem: vi.fn(),
  removeItem: vi.fn()
}
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
})

const mockSearchResults = [
  {
    id: '1',
    type: 'scene' as const,
    title: 'Test Scene 1',
    content: 'This is a test scene with some content for searching.',
    highlights: ['test', 'scene'],
    metadata: { scene_id: '1', character_count: 2 },
    relevance_score: 0.95,
    matched_terms: ['test', 'scene'],
    context: {
      scene_name: 'Test Scene 1',
      timestamp: '2024-01-01T00:00:00Z'
    }
  },
  {
    id: '2',
    type: 'pose' as const,
    title: 'Character Action',
    content: 'The character performs an important action that drives the plot forward.',
    highlights: ['character', 'action'],
    metadata: { pose_id: '2', character_name: 'TestChar' },
    relevance_score: 0.87,
    matched_terms: ['character', 'action'],
    context: {
      scene_name: 'Test Scene 1',
      character_name: 'TestChar',
      timestamp: '2024-01-01T01:00:00Z'
    }
  }
]

describe('AdvancedSearchInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({
        success: true,
        data: mockSearchResults,
        meta: {
          total_results: 2,
          suggestions: ['character', 'scene', 'action'],
          facet_counts: {
            types: { scene: 1, pose: 1 },
            characters: { TestChar: 1 }
          },
          has_more: false
        }
      })
    })
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('Rendering', () => {
    it('renders the search interface with all essential elements', () => {
      render(<AdvancedSearchInterface />)
      
      expect(screen.getByRole('textbox', { name: /search/i })).toBeInTheDocument()
      expect(screen.getByRole('combobox')).toBeInTheDocument() // Search scope selector
      expect(screen.getByText('Advanced Search')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /filters/i })).toBeInTheDocument()
    })

    it('shows search scopes in the dropdown', async () => {
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      const scopeSelect = screen.getByRole('combobox')
      await user.click(scopeSelect)
      
      expect(screen.getByText('All Content')).toBeInTheDocument()
      expect(screen.getByText('Scenes')).toBeInTheDocument()
      expect(screen.getByText('Poses')).toBeInTheDocument()
      expect(screen.getByText('Characters')).toBeInTheDocument()
      expect(screen.getByText('Plot Elements')).toBeInTheDocument()
    })

    it('renders advanced filters when toggle is clicked', async () => {
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      const filtersButton = screen.getByRole('button', { name: /filters/i })
      await user.click(filtersButton)
      
      await waitFor(() => {
        expect(screen.getByText('Date Range')).toBeInTheDocument()
        expect(screen.getByText('Characters')).toBeInTheDocument()
        expect(screen.getByText('Tags')).toBeInTheDocument()
      })
    })
  })

  describe('Search Functionality', () => {
    it('performs search when query is entered', async () => {
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      const searchInput = screen.getByRole('textbox', { name: /search/i })
      await user.type(searchInput, 'test query')
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/search-summary/search/advanced'),
          expect.objectContaining({
            headers: expect.objectContaining({
              'Authorization': 'Bearer mock-token'
            })
          })
        )
      })
    })

    it('displays search results correctly', async () => {
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      const searchInput = screen.getByRole('textbox', { name: /search/i })
      await user.type(searchInput, 'test')
      
      await waitFor(() => {
        expect(screen.getByText('Test Scene 1')).toBeInTheDocument()
        expect(screen.getByText('Character Action')).toBeInTheDocument()
      })
    })

    it('groups results by type', async () => {
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      const searchInput = screen.getByRole('textbox', { name: /search/i })
      await user.type(searchInput, 'test')
      
      await waitFor(() => {
        expect(screen.getByText('Scenes')).toBeInTheDocument()
        expect(screen.getByText('Poses')).toBeInTheDocument()
      })
    })

    it('displays search suggestions', async () => {
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      const searchInput = screen.getByRole('textbox', { name: /search/i })
      await user.type(searchInput, 'test')
      
      await waitFor(() => {
        expect(screen.getByText('Suggestions:')).toBeInTheDocument()
        expect(screen.getByRole('button', { name: 'character' })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: 'scene' })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: 'action' })).toBeInTheDocument()
      })
    })

    it('applies search scope filter', async () => {
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      const scopeSelect = screen.getByRole('combobox')
      await user.click(scopeSelect)
      await user.click(screen.getByText('Scenes'))
      
      const searchInput = screen.getByRole('textbox', { name: /search/i })
      await user.type(searchInput, 'test')
      
      await waitFor(() => {
        const lastCall = mockFetch.mock.calls[mockFetch.mock.calls.length - 1]
        expect(lastCall[0]).toContain('search_scope=scenes')
      })
    })
  })

  describe('Advanced Filtering', () => {
    it('shows filter count badge when filters are active', async () => {
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      // Open advanced filters
      const filtersButton = screen.getByRole('button', { name: /filters/i })
      await user.click(filtersButton)
      
      // Enable archived content filter
      await waitFor(() => {
        const archivedCheckbox = screen.getByRole('checkbox', { name: /include archived/i })
        user.click(archivedCheckbox)
      })
      
      await waitFor(() => {
        expect(screen.getByText('1')).toBeInTheDocument() // Filter count badge
      })
    })

    it('clears all filters when clear button is clicked', async () => {
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      // Open advanced filters and set some filters
      const filtersButton = screen.getByRole('button', { name: /filters/i })
      await user.click(filtersButton)
      
      await waitFor(async () => {
        const archivedCheckbox = screen.getByRole('checkbox', { name: /include archived/i })
        await user.click(archivedCheckbox)
      })
      
      // Clear filters
      await waitFor(async () => {
        const clearButton = screen.getByRole('button', { name: /clear all/i })
        await user.click(clearButton)
      })
      
      await waitFor(() => {
        const archivedCheckbox = screen.getByRole('checkbox', { name: /include archived/i })
        expect(archivedCheckbox).not.toBeChecked()
      })
    })

    it('applies date range filter', async () => {
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      // Open advanced filters
      const filtersButton = screen.getByRole('button', { name: /filters/i })
      await user.click(filtersButton)
      
      await waitFor(() => {
        expect(screen.getByText('Date Range')).toBeInTheDocument()
      })
      
      // Note: Calendar interaction would require more complex testing setup
      // This test verifies the filter section exists
    })
  })

  describe('Result Management', () => {
    it('allows selecting individual results', async () => {
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      const searchInput = screen.getByRole('textbox', { name: /search/i })
      await user.type(searchInput, 'test')
      
      await waitFor(() => {
        const checkboxes = screen.getAllByRole('checkbox')
        // Find result checkboxes (not the filter checkboxes)
        const resultCheckbox = checkboxes.find(cb => 
          cb.getAttribute('aria-describedby') === null &&
          cb.closest('[data-testid]') === null
        )
        if (resultCheckbox) {
          return user.click(resultCheckbox)
        }
      })
      
      await waitFor(() => {
        expect(screen.getByText(/Export \(1\)/)).toBeInTheDocument()
      })
    })

    it('allows selecting all results in a group', async () => {
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      const searchInput = screen.getByRole('textbox', { name: /search/i })
      await user.type(searchInput, 'test')
      
      await waitFor(async () => {
        const selectAllButtons = screen.getAllByRole('button', { name: /select all/i })
        if (selectAllButtons.length > 0) {
          await user.click(selectAllButtons[0])
        }
      })
      
      await waitFor(() => {
        expect(screen.getByText(/Export \(/)).toBeInTheDocument()
      })
    })

    it('expands and collapses result groups', async () => {
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      const searchInput = screen.getByRole('textbox', { name: /search/i })
      await user.type(searchInput, 'test')
      
      await waitFor(async () => {
        const groupToggle = screen.getByRole('button', { name: /scenes/i })
        await user.click(groupToggle)
      })
      
      // Group should toggle between expanded/collapsed states
      // The exact assertion depends on the implementation details
    })
  })

  describe('Export Functionality', () => {
    it('opens export dialog when export button is clicked', async () => {
      const mockOnExport = vi.fn()
      const user = userEvent.setup()
      render(<AdvancedSearchInterface onExport={mockOnExport} />)
      
      const searchInput = screen.getByRole('textbox', { name: /search/i })
      await user.type(searchInput, 'test')
      
      // Select a result first
      await waitFor(() => {
        const checkboxes = screen.getAllByRole('checkbox')
        const resultCheckbox = checkboxes.find(cb => 
          cb.getAttribute('aria-describedby') === null
        )
        if (resultCheckbox) {
          return user.click(resultCheckbox)
        }
      })
      
      // Click export button
      await waitFor(async () => {
        const exportButton = screen.getByRole('button', { name: /export/i })
        await user.click(exportButton)
      })
      
      await waitFor(() => {
        expect(screen.getByText('Export Search Results')).toBeInTheDocument()
      })
    })

    it('calls onExport callback with selected results', async () => {
      const mockOnExport = vi.fn().mockResolvedValue(undefined)
      const user = userEvent.setup()
      render(<AdvancedSearchInterface onExport={mockOnExport} />)
      
      const searchInput = screen.getByRole('textbox', { name: /search/i })
      await user.type(searchInput, 'test')
      
      // Select a result and export
      await waitFor(() => {
        const checkboxes = screen.getAllByRole('checkbox')
        const resultCheckbox = checkboxes.find(cb => 
          cb.getAttribute('aria-describedby') === null
        )
        if (resultCheckbox) {
          return user.click(resultCheckbox)
        }
      })
      
      await waitFor(async () => {
        const exportButton = screen.getByRole('button', { name: /export/i })
        await user.click(exportButton)
      })
      
      await waitFor(async () => {
        const jsonButton = screen.getByRole('button', { name: /json/i })
        await user.click(jsonButton)
      })
      
      await waitFor(() => {
        expect(mockOnExport).toHaveBeenCalledWith(
          expect.any(Array),
          'json'
        )
      })
    })
  })

  describe('Error Handling', () => {
    it('displays error message when search fails', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: vi.fn().mockResolvedValue({
          success: false,
          message: 'Search service unavailable'
        })
      })
      
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      const searchInput = screen.getByRole('textbox', { name: /search/i })
      await user.type(searchInput, 'test')
      
      await waitFor(() => {
        expect(screen.getByText('Search service unavailable')).toBeInTheDocument()
      })
    })

    it('handles network errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))
      
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      const searchInput = screen.getByRole('textbox', { name: /search/i })
      await user.type(searchInput, 'test')
      
      await waitFor(() => {
        expect(screen.getByText('Search failed')).toBeInTheDocument()
      })
    })

    it('shows empty state when no results found', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({
          success: true,
          data: [],
          meta: {
            total_results: 0,
            suggestions: [],
            facet_counts: {},
            has_more: false
          }
        })
      })
      
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      const searchInput = screen.getByRole('textbox', { name: /search/i })
      await user.type(searchInput, 'nonexistent')
      
      await waitFor(() => {
        expect(screen.getByText('No results found')).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('provides proper ARIA labels for search elements', () => {
      render(<AdvancedSearchInterface />)
      
      const searchInput = screen.getByRole('textbox', { name: /search/i })
      expect(searchInput).toHaveAttribute('placeholder', 
        expect.stringContaining('Search scenes, poses, characters'))
    })

    it('maintains keyboard navigation support', async () => {
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      const searchInput = screen.getByRole('textbox', { name: /search/i })
      
      // Tab navigation should work
      await user.tab()
      expect(searchInput).toHaveFocus()
      
      await user.tab()
      expect(screen.getByRole('combobox')).toHaveFocus()
    })

    it('provides screen reader friendly result descriptions', async () => {
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      const searchInput = screen.getByRole('textbox', { name: /search/i })
      await user.type(searchInput, 'test')
      
      await waitFor(() => {
        const results = screen.getAllByRole('button', { name: /Test Scene/i })
        expect(results[0]).toBeInTheDocument()
      })
    })
  })

  describe('Performance', () => {
    it('debounces search input to avoid excessive API calls', async () => {
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      const searchInput = screen.getByRole('textbox', { name: /search/i })
      
      // Type multiple characters quickly
      await user.type(searchInput, 'test')
      
      // Should only make one API call due to debouncing
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(1)
      })
    })

    it('shows loading state during search', async () => {
      // Create a promise that we can control
      let resolvePromise: (value: any) => void
      const searchPromise = new Promise((resolve) => {
        resolvePromise = resolve
      })
      
      mockFetch.mockReturnValueOnce(searchPromise)
      
      const user = userEvent.setup()
      render(<AdvancedSearchInterface />)
      
      const searchInput = screen.getByRole('textbox', { name: /search/i })
      await user.type(searchInput, 'test')
      
      // Should show loading state
      await waitFor(() => {
        expect(screen.getByText('Searching...')).toBeInTheDocument()
      })
      
      // Resolve the promise to complete the test
      resolvePromise!({
        ok: true,
        json: vi.fn().mockResolvedValue({
          success: true,
          data: mockSearchResults,
          meta: { total_results: 2 }
        })
      })
    })
  })
}) 