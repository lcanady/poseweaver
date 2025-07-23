import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { CharacterConsistencyScoreDisplay } from '@/components/continuity/character-consistency-score-display'
import { useToast } from '@/hooks/use-toast'

// Mock the toast hook
jest.mock('@/hooks/use-toast')
const mockToast = jest.fn()
;(useToast as jest.Mock).mockReturnValue({ toast: mockToast })

// Mock fetch
global.fetch = jest.fn()

const mockCharacterConsistencyData = {
  character_id: 'char-1',
  character_name: 'John Doe',
  consistency_score: 85,
  recent_inconsistencies: [
    {
      id: 'inc-1',
      timestamp: '2023-11-15T10:30:00Z',
      description: 'Character displayed different personality traits than established',
      severity: 'medium' as const,
      pose_id: 'pose-123',
      resolved: false
    },
    {
      id: 'inc-2', 
      timestamp: '2023-11-14T15:45:00Z',
      description: 'Inconsistent knowledge about past events',
      severity: 'high' as const,
      pose_id: 'pose-124',
      resolved: false
    },
    {
      id: 'inc-3',
      timestamp: '2023-11-13T08:20:00Z', 
      description: 'Minor inconsistency in character background details',
      severity: 'low' as const,
      pose_id: 'pose-125',
      resolved: true
    }
  ]
}

const mockProps = {
  ...mockCharacterConsistencyData,
  onInconsistencyClick: jest.fn()
}

describe('CharacterConsistencyScoreDisplay', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(fetch as jest.Mock).mockClear()
  })

  it('renders component with character name and consistency score', () => {
    render(<CharacterConsistencyScoreDisplay {...mockProps} />)
    
    expect(screen.getByText('Character Consistency')).toBeInTheDocument()
    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.getByText('85%')).toBeInTheDocument()
    expect(screen.getByText('Good')).toBeInTheDocument()
  })

  it('displays correct consistency score color and label', () => {
    const highScoreProps = { ...mockProps, consistency_score: 95 }
    const { rerender } = render(<CharacterConsistencyScoreDisplay {...highScoreProps} />)
    expect(screen.getByText('Excellent')).toBeInTheDocument()

    const lowScoreProps = { ...mockProps, consistency_score: 55 }
    rerender(<CharacterConsistencyScoreDisplay {...lowScoreProps} />)
    expect(screen.getByText('Poor')).toBeInTheDocument()
  })

  it('shows correct count of active and resolved issues', () => {
    render(<CharacterConsistencyScoreDisplay {...mockProps} />)
    
    expect(screen.getByText('Active Issues (2)')).toBeInTheDocument()
    expect(screen.getByText('Resolved (1)')).toBeInTheDocument()
  })

  it('displays unresolved inconsistencies with correct severity badges', () => {
    render(<CharacterConsistencyScoreDisplay {...mockProps} />)
    
    const activeTab = screen.getByRole('tab', { name: /Active Issues/ })
    fireEvent.click(activeTab)

    expect(screen.getByText('Character displayed different personality traits than established')).toBeInTheDocument()
    expect(screen.getByText('Inconsistent knowledge about past events')).toBeInTheDocument()
    expect(screen.getByText('MEDIUM')).toBeInTheDocument()
    expect(screen.getByText('HIGH')).toBeInTheDocument()
  })

  it('displays resolved inconsistencies in resolved tab', () => {
    render(<CharacterConsistencyScoreDisplay {...mockProps} />)
    
    const resolvedTab = screen.getByRole('tab', { name: /Resolved/ })
    fireEvent.click(resolvedTab)

    expect(screen.getByText('Minor inconsistency in character background details')).toBeInTheDocument()
    expect(screen.getByText('RESOLVED')).toBeInTheDocument()
  })

  it('calls onInconsistencyClick when view pose button is clicked', () => {
    render(<CharacterConsistencyScoreDisplay {...mockProps} />)
    
    const viewButtons = screen.getAllByTitle('View Pose')
    fireEvent.click(viewButtons[0])
    
    expect(mockProps.onInconsistencyClick).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'inc-1' })
    )
  })

  it('opens resolution dialog when resolve button is clicked', () => {
    render(<CharacterConsistencyScoreDisplay {...mockProps} />)
    
    const resolveButtons = screen.getAllByText('Resolve')
    fireEvent.click(resolveButtons[0])
    
    expect(screen.getByText('Resolve Inconsistency')).toBeInTheDocument()
    expect(screen.getByText('Character displayed different personality traits than established')).toBeInTheDocument()
  })

  it('submits resolution when form is filled and submitted', async () => {
    const mockFetchResponse = { ok: true }
    ;(fetch as jest.Mock).mockResolvedValueOnce(mockFetchResponse)
    Object.defineProperty(window, 'location', {
      value: { reload: jest.fn() },
      writable: true
    })

    render(<CharacterConsistencyScoreDisplay {...mockProps} />)
    
    const resolveButtons = screen.getAllByText('Resolve')
    fireEvent.click(resolveButtons[0])
    
    const resolutionInput = screen.getByPlaceholderText('Explain how this inconsistency was resolved...')
    fireEvent.change(resolutionInput, { target: { value: 'This was addressed in scene discussion' } })
    
    const submitButton = screen.getByRole('button', { name: /Resolve/ })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/character-plot-tracking/resolve-inconsistency'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify({
            character_id: 'char-1',
            inconsistency_id: 'inc-1',
            resolution: 'This was addressed in scene discussion'
          })
        })
      )
    })

    expect(mockToast).toHaveBeenCalledWith({
      title: 'Inconsistency Resolved',
      description: 'The inconsistency has been marked as resolved.'
    })
  })

  it('shows error toast when resolution submission fails', async () => {
    const mockFetchResponse = { ok: false }
    ;(fetch as jest.Mock).mockResolvedValueOnce(mockFetchResponse)

    render(<CharacterConsistencyScoreDisplay {...mockProps} />)
    
    const resolveButtons = screen.getAllByText('Resolve')
    fireEvent.click(resolveButtons[0])
    
    const resolutionInput = screen.getByPlaceholderText('Explain how this inconsistency was resolved...')
    fireEvent.change(resolutionInput, { target: { value: 'Test resolution' } })
    
    const submitButton = screen.getByRole('button', { name: /Resolve/ })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Resolution Failed',
        description: 'Failed to resolve inconsistency. Please try again.',
        variant: 'destructive'
      })
    })
  })

  it('shows overview statistics correctly', () => {
    render(<CharacterConsistencyScoreDisplay {...mockProps} />)
    
    const overviewTab = screen.getByRole('tab', { name: /Overview/ })
    fireEvent.click(overviewTab)

    expect(screen.getByText('3')).toBeInTheDocument() // Total Issues
    expect(screen.getByText('2')).toBeInTheDocument() // Active Issues
    expect(screen.getByText('33%')).toBeInTheDocument() // Resolution Rate (1/3)
  })

  it('displays severity breakdown in overview', () => {
    render(<CharacterConsistencyScoreDisplay {...mockProps} />)
    
    const overviewTab = screen.getByRole('tab', { name: /Overview/ })
    fireEvent.click(overviewTab)

    expect(screen.getByText('High Severity Issues')).toBeInTheDocument()
    expect(screen.getByText('Medium Severity Issues')).toBeInTheDocument() 
    expect(screen.getByText('Low Severity Issues')).toBeInTheDocument()
  })

  it('handles empty inconsistencies list', () => {
    const emptyProps = {
      ...mockProps,
      recent_inconsistencies: []
    }
    
    render(<CharacterConsistencyScoreDisplay {...emptyProps} />)
    
    expect(screen.getByText('No Active Issues')).toBeInTheDocument()
    expect(screen.getByText('This character has no unresolved consistency issues.')).toBeInTheDocument()
  })

  it('validates resolution input before submission', () => {
    render(<CharacterConsistencyScoreDisplay {...mockProps} />)
    
    const resolveButtons = screen.getAllByText('Resolve')
    fireEvent.click(resolveButtons[0])
    
    const submitButton = screen.getByRole('button', { name: /Resolve/ })
    fireEvent.click(submitButton)

    expect(mockToast).toHaveBeenCalledWith({
      title: 'Resolution Required',
      description: 'Please provide a resolution explanation.',
      variant: 'destructive'
    })
  })

  it('shows loading state during resolution submission', async () => {
    const mockFetchResponse = { ok: true }
    ;(fetch as jest.Mock).mockImplementation(() => new Promise(resolve => 
      setTimeout(() => resolve(mockFetchResponse), 100)
    ))

    render(<CharacterConsistencyScoreDisplay {...mockProps} />)
    
    const resolveButtons = screen.getAllByText('Resolve')
    fireEvent.click(resolveButtons[0])
    
    const resolutionInput = screen.getByPlaceholderText('Explain how this inconsistency was resolved...')
    fireEvent.change(resolutionInput, { target: { value: 'Test resolution' } })
    
    const submitButton = screen.getByRole('button', { name: /Resolve/ })
    fireEvent.click(submitButton)

    expect(screen.getByText('Resolving...')).toBeInTheDocument()
    
    await waitFor(() => {
      expect(screen.queryByText('Resolving...')).not.toBeInTheDocument()
    }, { timeout: 200 })
  })
}) 