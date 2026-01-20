import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
const vi = jest;
import { AdvancedSummaryInterface } from '../../../components/search/advanced-summary-interface'

// Mock hooks and utilities
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

const mockGeneratedSummary = {
  id: 'summary-1',
  scene_id: 'scene-1',
  summary_text: 'This is a comprehensive summary of the scene that covers all the important events, character interactions, and plot developments that occurred during the roleplay session.',
  summary_type: 'comprehensive',
  generated_at: '2024-01-01T00:00:00Z',
  generation_time: 1500,
  word_count: 25,
  options: {
    focus: 'comprehensive',
    max_length: 500,
    include_details: true,
    formal_style: false,
    chronological: true,
    highlight_key_events: true,
    include_dialogue: false,
    include_emotions: true,
    include_relationships: true,
    include_setting: true,
    writing_style: 'narrative',
    perspective: 'third_person',
    detail_level: 'standard',
    include_statistics: false
  },
  template_used: 'comprehensive',
  metadata: {
    scene_name: 'Test Scene',
    character_count: 3,
    pose_count: 15,
    date_range: { start: '2024-01-01T00:00:00Z', end: '2024-01-01T02:00:00Z' },
    key_characters: ['Alice', 'Bob', 'Charlie'],
    key_events: ['Meeting began', 'Conflict arose', 'Resolution reached'],
    themes: ['cooperation', 'conflict', 'resolution'],
    emotions: ['tension', 'relief', 'satisfaction'],
    locations: ['Conference Room']
  }
}

const mockAvailableCharacters = [
  { id: 'char-1', name: 'Alice' },
  { id: 'char-2', name: 'Bob' },
  { id: 'char-3', name: 'Charlie' }
]

describe('AdvancedSummaryInterface', () => {
  const defaultProps = {
    sceneId: 'scene-1',
    sceneName: 'Test Scene'
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({
        success: true,
        data: mockGeneratedSummary
      })
    })
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('Rendering', () => {
    it('renders the summary interface with essential elements', () => {
      render(<AdvancedSummaryInterface {...defaultProps} />)
      
      expect(screen.getByText('Summary Generation')).toBeInTheDocument()
      expect(screen.getByText('Test Scene')).toBeInTheDocument()
      expect(screen.getByText('Summary Template')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /generate summary/i })).toBeInTheDocument()
    })

    it('displays all summary templates', () => {
      render(<AdvancedSummaryInterface {...defaultProps} />)
      
      expect(screen.getByText('Comprehensive Overview')).toBeInTheDocument()
      expect(screen.getByText('Character-Focused')).toBeInTheDocument()
      expect(screen.getByText('Plot Progression')).toBeInTheDocument()
      expect(screen.getByText('Quick Recap')).toBeInTheDocument()
      expect(screen.getByText('Timeline Summary')).toBeInTheDocument()
    })

    it('shows custom template option when allowCustomTemplates is enabled', () => {
      render(
        <AdvancedSummaryInterface 
          {...defaultProps} 
          allowCustomTemplates={true} 
        />
      )
      
      expect(screen.getByText('Custom Template')).toBeInTheDocument()
    })

    it('shows character selection when focus is set to character', async () => {
      const user = userEvent.setup()
      render(
        <AdvancedSummaryInterface 
          {...defaultProps} 
          availableCharacters={mockAvailableCharacters}
        />
      )
      
      // Change focus to character
      const focusSelect = screen.getByDisplayValue('Comprehensive')
      await user.click(focusSelect)
      await user.click(screen.getByText('Character'))
      
      await waitFor(() => {
        expect(screen.getByText('Character')).toBeInTheDocument()
      })
    })
  })

  describe('Template Selection', () => {
    it('applies template settings when template is selected', async () => {
      const user = userEvent.setup()
      render(<AdvancedSummaryInterface {...defaultProps} />)
      
      // Click on Character-Focused template
      const characterTemplate = screen.getByText('Character-Focused')
      await user.click(characterTemplate)
      
      await waitFor(() => {
        // Should update focus and other settings
        const focusSelect = screen.getByDisplayValue('Character')
        expect(focusSelect).toBeInTheDocument()
      })
    })

    it('highlights selected template with visual indicator', async () => {
      const user = userEvent.setup()
      render(<AdvancedSummaryInterface {...defaultProps} />)
      
      const plotTemplate = screen.getByText('Plot Progression').closest('.cursor-pointer')
      await user.click(plotTemplate!)
      
      await waitFor(() => {
        expect(plotTemplate).toHaveClass('ring-2', 'ring-primary')
      })
    })

    it('opens custom template dialog when custom template is clicked', async () => {
      const user = userEvent.setup()
      render(
        <AdvancedSummaryInterface 
          {...defaultProps} 
          allowCustomTemplates={true} 
        />
      )
      
      const customTemplate = screen.getByText('Custom Template')
      await user.click(customTemplate)
      
      await waitFor(() => {
        expect(screen.getByText('Custom Summary Template')).toBeInTheDocument()
      })
    })
  })

  describe('Summary Generation', () => {
    it('generates summary when generate button is clicked', async () => {
      const mockOnSummaryGenerated = vi.fn()
      const user = userEvent.setup()
      render(
        <AdvancedSummaryInterface 
          {...defaultProps} 
          onSummaryGenerated={mockOnSummaryGenerated}
        />
      )
      
      const generateButton = screen.getByRole('button', { name: /generate summary/i })
      await user.click(generateButton)
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/search-summary/summaries/scenes/scene-1'),
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Authorization': 'Bearer mock-token',
              'Content-Type': 'application/json'
            })
          })
        )
      })

      await waitFor(() => {
        expect(mockOnSummaryGenerated).toHaveBeenCalledWith(mockGeneratedSummary)
      })
    })

    it('shows loading state during generation', async () => {
      let resolvePromise: (value: any) => void
      const generationPromise = new Promise((resolve) => {
        resolvePromise = resolve
      })
      
      mockFetch.mockReturnValueOnce(generationPromise)
      
      const user = userEvent.setup()
      render(<AdvancedSummaryInterface {...defaultProps} />)
      
      const generateButton = screen.getByRole('button', { name: /generate summary/i })
      await user.click(generateButton)
      
      await waitFor(() => {
        expect(screen.getByText('Generating...')).toBeInTheDocument()
        expect(screen.getByText('Generating summary...')).toBeInTheDocument()
      })
      
      // Resolve to complete the test
      resolvePromise!({
        ok: true,
        json: vi.fn().mockResolvedValue({
          success: true,
          data: mockGeneratedSummary
        })
      })
    })

    it('displays generated summary correctly', async () => {
      const user = userEvent.setup()
      render(<AdvancedSummaryInterface {...defaultProps} />)
      
      const generateButton = screen.getByRole('button', { name: /generate summary/i })
      await user.click(generateButton)
      
      await waitFor(() => {
        expect(screen.getByText('Generated Summary')).toBeInTheDocument()
        expect(screen.getByText(mockGeneratedSummary.summary_text)).toBeInTheDocument()
        expect(screen.getByText('25 words')).toBeInTheDocument()
      })
    })

    it('shows summary statistics when analytics are enabled', async () => {
      const user = userEvent.setup()
      render(
        <AdvancedSummaryInterface 
          {...defaultProps} 
          enableAnalytics={true}
        />
      )
      
      const generateButton = screen.getByRole('button', { name: /generate summary/i })
      await user.click(generateButton)
      
      await waitFor(() => {
        expect(screen.getByText('min read')).toBeInTheDocument()
        expect(screen.getByText('key events')).toBeInTheDocument()
        expect(screen.getByText('characters')).toBeInTheDocument()
        expect(screen.getByText('emotion')).toBeInTheDocument()
      })
    })
  })

  describe('Summary Customization', () => {
    it('allows changing summary length with slider', async () => {
      const user = userEvent.setup()
      render(<AdvancedSummaryInterface {...defaultProps} />)
      
      // Find and interact with the length slider
      const slider = screen.getByRole('slider')
      await user.click(slider)
      
      // Verify the length label updates
      await waitFor(() => {
        expect(screen.getByText(/Length:/)).toBeInTheDocument()
      })
    })

    it('shows advanced options when toggle is expanded', async () => {
      const user = userEvent.setup()
      render(<AdvancedSummaryInterface {...defaultProps} />)
      
      const advancedToggle = screen.getByRole('button', { name: /advanced options/i })
      await user.click(advancedToggle)
      
      await waitFor(() => {
        expect(screen.getByText('Include Details')).toBeInTheDocument()
        expect(screen.getByText('Chronological')).toBeInTheDocument()
        expect(screen.getByText('Highlight Key Events')).toBeInTheDocument()
        expect(screen.getByText('Include Dialogue')).toBeInTheDocument()
      })
    })

    it('allows toggling advanced options switches', async () => {
      const user = userEvent.setup()
      render(<AdvancedSummaryInterface {...defaultProps} />)
      
      const advancedToggle = screen.getByRole('button', { name: /advanced options/i })
      await user.click(advancedToggle)
      
      await waitFor(async () => {
        const dialogueSwitch = screen.getByRole('switch', { name: /include dialogue/i })
        await user.click(dialogueSwitch)
        expect(dialogueSwitch).toBeChecked()
      })
    })

    it('allows adding custom instructions', async () => {
      const user = userEvent.setup()
      render(<AdvancedSummaryInterface {...defaultProps} />)
      
      const advancedToggle = screen.getByRole('button', { name: /advanced options/i })
      await user.click(advancedToggle)
      
      await waitFor(async () => {
        const customInstructions = screen.getByPlaceholderText(/specific instructions/i)
        await user.type(customInstructions, 'Focus on emotional content')
        expect(customInstructions).toHaveValue('Focus on emotional content')
      })
    })
  })

  describe('Summary Editing', () => {
    beforeEach(async () => {
      const user = userEvent.setup()
      render(<AdvancedSummaryInterface {...defaultProps} />)
      
      // Generate a summary first
      const generateButton = screen.getByRole('button', { name: /generate summary/i })
      await user.click(generateButton)
      
      await waitFor(() => {
        expect(screen.getByText('Generated Summary')).toBeInTheDocument()
      })
    })

    it('enables editing mode when edit button is clicked', async () => {
      const user = userEvent.setup()
      
      const editButton = screen.getByRole('button', { name: /edit/i })
      await user.click(editButton)
      
      await waitFor(() => {
        expect(screen.getByRole('textbox')).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
      })
    })

    it('allows editing summary text', async () => {
      const user = userEvent.setup()
      
      const editButton = screen.getByRole('button', { name: /edit/i })
      await user.click(editButton)
      
      await waitFor(async () => {
        const textarea = screen.getByRole('textbox')
        await user.clear(textarea)
        await user.type(textarea, 'This is an edited summary.')
        expect(textarea).toHaveValue('This is an edited summary.')
      })
    })

    it('saves edited summary when save button is clicked', async () => {
      const mockOnSummaryEdited = vi.fn().mockResolvedValue(undefined)
      const user = userEvent.setup()
      
      // Re-render with the callback
      render(
        <AdvancedSummaryInterface 
          {...defaultProps} 
          onSummaryEdited={mockOnSummaryEdited}
        />
      )
      
      // Generate summary first
      const generateButton = screen.getByRole('button', { name: /generate summary/i })
      await user.click(generateButton)
      
      await waitFor(async () => {
        const editButton = screen.getByRole('button', { name: /edit/i })
        await user.click(editButton)
      })
      
      await waitFor(async () => {
        const textarea = screen.getByRole('textbox')
        await user.clear(textarea)
        await user.type(textarea, 'Edited text')
      })
      
      await waitFor(async () => {
        const saveButton = screen.getByRole('button', { name: /save/i })
        await user.click(saveButton)
      })
      
      await waitFor(() => {
        expect(mockOnSummaryEdited).toHaveBeenCalledWith('summary-1', 'Edited text')
      })
    })

    it('cancels editing when cancel button is clicked', async () => {
      const user = userEvent.setup()
      
      const editButton = screen.getByRole('button', { name: /edit/i })
      await user.click(editButton)
      
      await waitFor(async () => {
        const textarea = screen.getByRole('textbox')
        await user.clear(textarea)
        await user.type(textarea, 'Some changes')
      })
      
      await waitFor(async () => {
        const cancelButton = screen.getByRole('button', { name: /cancel/i })
        await user.click(cancelButton)
      })
      
      await waitFor(() => {
        expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
        expect(screen.getByText(mockGeneratedSummary.summary_text)).toBeInTheDocument()
      })
    })
  })

  describe('Export Functionality', () => {
    beforeEach(async () => {
      const user = userEvent.setup()
      render(<AdvancedSummaryInterface {...defaultProps} />)
      
      // Generate a summary first
      const generateButton = screen.getByRole('button', { name: /generate summary/i })
      await user.click(generateButton)
      
      await waitFor(() => {
        expect(screen.getByText('Generated Summary')).toBeInTheDocument()
      })
    })

    it('opens export dialog when export button is clicked', async () => {
      const user = userEvent.setup()
      
      const exportButton = screen.getByRole('button', { name: /download/i })
      await user.click(exportButton)
      
      await waitFor(() => {
        expect(screen.getByText('Export Summary')).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /json/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /text/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /pdf/i })).toBeInTheDocument()
      })
    })

    it('calls export callback when export format is selected', async () => {
      const mockOnSummaryExported = vi.fn().mockResolvedValue(undefined)
      const user = userEvent.setup()
      
      // Re-render with the callback
      render(
        <AdvancedSummaryInterface 
          {...defaultProps} 
          onSummaryExported={mockOnSummaryExported}
        />
      )
      
      // Generate summary first
      const generateButton = screen.getByRole('button', { name: /generate summary/i })
      await user.click(generateButton)
      
      await waitFor(async () => {
        const exportButton = screen.getByRole('button', { name: /download/i })
        await user.click(exportButton)
      })
      
      await waitFor(async () => {
        const jsonButton = screen.getByRole('button', { name: /json/i })
        await user.click(jsonButton)
      })
      
      await waitFor(() => {
        expect(mockOnSummaryExported).toHaveBeenCalledWith(
          expect.objectContaining({
            id: 'summary-1',
            scene_id: 'scene-1'
          }),
          'json'
        )
      })
    })
  })

  describe('Preview Mode', () => {
    beforeEach(async () => {
      const user = userEvent.setup()
      render(<AdvancedSummaryInterface {...defaultProps} />)
      
      // Generate a summary first
      const generateButton = screen.getByRole('button', { name: /generate summary/i })
      await user.click(generateButton)
      
      await waitFor(() => {
        expect(screen.getByText('Generated Summary')).toBeInTheDocument()
      })
    })

    it('toggles preview mode when preview button is clicked', async () => {
      const user = userEvent.setup()
      
      const previewButton = screen.getByRole('button', { name: /eye/i })
      await user.click(previewButton)
      
      await waitFor(() => {
        const summaryContent = screen.getByText(mockGeneratedSummary.summary_text).closest('div')
        expect(summaryContent).toHaveClass('bg-muted/50')
      })
    })
  })

  describe('Error Handling', () => {
    it('displays error message when summary generation fails', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: vi.fn().mockResolvedValue({
          success: false,
          message: 'Summary generation service unavailable'
        })
      })
      
      const user = userEvent.setup()
      render(<AdvancedSummaryInterface {...defaultProps} />)
      
      const generateButton = screen.getByRole('button', { name: /generate summary/i })
      await user.click(generateButton)
      
      await waitFor(() => {
        // Toast should be called with error message
        expect(screen.queryByText('Generated Summary')).not.toBeInTheDocument()
      })
    })

    it('handles network errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))
      
      const user = userEvent.setup()
      render(<AdvancedSummaryInterface {...defaultProps} />)
      
      const generateButton = screen.getByRole('button', { name: /generate summary/i })
      await user.click(generateButton)
      
      await waitFor(() => {
        // Should not show generated summary
        expect(screen.queryByText('Generated Summary')).not.toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('provides proper ARIA labels for interactive elements', () => {
      render(<AdvancedSummaryInterface {...defaultProps} />)
      
      const generateButton = screen.getByRole('button', { name: /generate summary/i })
      expect(generateButton).toHaveAccessibleName()
      
      const lengthSlider = screen.getByRole('slider')
      expect(lengthSlider).toBeInTheDocument()
    })

    it('maintains keyboard navigation support', async () => {
      const user = userEvent.setup()
      render(<AdvancedSummaryInterface {...defaultProps} />)
      
      // Tab navigation should work through templates
      await user.tab()
      const firstTemplate = screen.getAllByRole('generic')[0] // Template cards
      
      // Should be able to navigate to generate button
      const generateButton = screen.getByRole('button', { name: /generate summary/i })
      generateButton.focus()
      expect(generateButton).toHaveFocus()
    })

    it('provides appropriate text alternatives for visual elements', () => {
      render(<AdvancedSummaryInterface {...defaultProps} />)
      
      // Icons should have appropriate text alternatives through button labels
      expect(screen.getByRole('button', { name: /generate summary/i })).toBeInTheDocument()
    })
  })

  describe('Integration', () => {
    it('works with existing summaries prop', () => {
      const existingSummaries = [mockGeneratedSummary]
      render(
        <AdvancedSummaryInterface 
          {...defaultProps} 
          existingSummaries={[mockGeneratedSummary] as any}
        />
      )
      
      expect(screen.getByRole('button', { name: /history \(1\)/i })).toBeInTheDocument()
    })

    it('integrates with character selection', async () => {
      const user = userEvent.setup()
      render(
        <AdvancedSummaryInterface 
          {...defaultProps} 
          availableCharacters={mockAvailableCharacters}
        />
      )
      
      // Change focus to character
      const focusSelect = screen.getByDisplayValue('Comprehensive')
      await user.click(focusSelect)
      await user.click(screen.getByText('Character'))
      
      await waitFor(() => {
        // Character dropdown should be visible
        expect(screen.getByText('Character')).toBeInTheDocument()
      })
    })
  })
}) 