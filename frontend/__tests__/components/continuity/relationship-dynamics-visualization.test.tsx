import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { RelationshipDynamicsVisualization } from '@/components/continuity/relationship-dynamics-visualization'

const mockRelationships = [
  {
    relationship_id: 'rel-1',
    character_id: 'char-1',
    character_name: 'John Doe',
    related_character_id: 'char-2',
    related_character_name: 'Jane Smith',
    relationship_type: 'friend',
    dynamics: [
      {
        timestamp: '2023-11-10T10:00:00Z',
        trust_level: 7,
        tension_level: 2,
        description: 'First meeting, positive interaction'
      },
      {
        timestamp: '2023-11-12T14:30:00Z',
        trust_level: 8,
        tension_level: 1,
        description: 'Worked together successfully'
      },
      {
        timestamp: '2023-11-15T09:15:00Z',
        trust_level: 9,
        tension_level: 1,
        description: 'Mutual respect established'
      }
    ]
  },
  {
    relationship_id: 'rel-2',
    character_id: 'char-1',
    character_name: 'John Doe',
    related_character_id: 'char-3',
    related_character_name: 'Bob Wilson',
    relationship_type: 'rival',
    dynamics: [
      {
        timestamp: '2023-11-11T11:20:00Z',
        trust_level: 3,
        tension_level: 8,
        description: 'Disagreement over strategy'
      },
      {
        timestamp: '2023-11-14T16:45:00Z',
        trust_level: 2,
        tension_level: 9,
        description: 'Open conflict during meeting'
      }
    ]
  }
]

const mockProps = {
  scene_id: 'scene-1',
  character_relationships: mockRelationships,
  onRelationshipClick: jest.fn(),
  compact: false
}

describe('RelationshipDynamicsVisualization', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders component with relationship count', () => {
    render(<RelationshipDynamicsVisualization {...mockProps} />)
    
    expect(screen.getByText('Relationship Dynamics')).toBeInTheDocument()
    expect(screen.getByText('2 relationships')).toBeInTheDocument()
  })

  it('displays overview statistics correctly', () => {
    render(<RelationshipDynamicsVisualization {...mockProps} />)
    
    // Should default to overview mode
    expect(screen.getByText('Total Relationships')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument() // Total count
    expect(screen.getByText('Avg Trust')).toBeInTheDocument()
    expect(screen.getByText('Avg Tension')).toBeInTheDocument()
  })

  it('switches to timeline view when timeline mode is selected', () => {
    render(<RelationshipDynamicsVisualization {...mockProps} />)
    
    const viewSelect = screen.getAllByRole('combobox')[1] // Second select is view mode
    fireEvent.click(viewSelect)
    
    const timelineOption = screen.getByText('Timeline')
    fireEvent.click(timelineOption)
    
    expect(screen.getByText('Select a Relationship')).toBeInTheDocument()
  })

  it('switches to matrix view when matrix mode is selected', () => {
    render(<RelationshipDynamicsVisualization {...mockProps} />)
    
    const viewSelect = screen.getAllByRole('combobox')[1] // Second select is view mode
    fireEvent.click(viewSelect)
    
    const matrixOption = screen.getByText('Matrix')
    fireEvent.click(matrixOption)
    
    expect(screen.getByText('Relationship Matrix')).toBeInTheDocument()
    expect(screen.getByText('Overview of all character relationships and their current dynamics')).toBeInTheDocument()
  })

  it('displays relationships in matrix view with correct information', () => {
    render(<RelationshipDynamicsVisualization {...mockProps} />)
    
    const viewSelect = screen.getAllByRole('combobox')[1]
    fireEvent.click(viewSelect)
    const matrixOption = screen.getByText('Matrix')
    fireEvent.click(matrixOption)
    
    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.getByText('2 relationships')).toBeInTheDocument()
    expect(screen.getByText('Jane Smith')).toBeInTheDocument()
    expect(screen.getByText('Bob Wilson')).toBeInTheDocument()
    expect(screen.getByText('friend')).toBeInTheDocument()
    expect(screen.getByText('rival')).toBeInTheDocument()
  })

  it('filters relationships by time range', () => {
    render(<RelationshipDynamicsVisualization {...mockProps} />)
    
    const timeRangeSelect = screen.getAllByRole('combobox')[0] // First select is time range
    fireEvent.click(timeRangeSelect)
    
    const oneWeekOption = screen.getByText('1 Week')
    fireEvent.click(oneWeekOption)
    
    // Should still show relationships that have recent dynamics
    expect(screen.getByText('2 relationships')).toBeInTheDocument()
  })

  it('shows timeline graph when relationship is selected', () => {
    render(<RelationshipDynamicsVisualization {...mockProps} />)
    
    // Switch to matrix view first
    const viewSelect = screen.getAllByRole('combobox')[1]
    fireEvent.click(viewSelect)
    const matrixOption = screen.getByText('Matrix')
    fireEvent.click(matrixOption)
    
    // Click on a relationship
    const relationshipCard = screen.getByText('Jane Smith').closest('div')
    if (relationshipCard) {
      fireEvent.click(relationshipCard)
      
      expect(screen.getByText('John Doe ↔ Jane Smith')).toBeInTheDocument()
      expect(screen.getByText('Relationship Dynamics Over Time')).toBeInTheDocument()
    }
  })

  it('displays recent events in timeline view', () => {
    render(<RelationshipDynamicsVisualization {...mockProps} />)
    
    // Switch to timeline view
    const viewSelect = screen.getAllByRole('combobox')[1]
    fireEvent.click(viewSelect)
    const timelineOption = screen.getByText('Timeline')
    fireEvent.click(timelineOption)
    
    // Switch to matrix to select relationship
    fireEvent.click(viewSelect)
    const matrixOption = screen.getByText('Matrix')
    fireEvent.click(matrixOption)
    
    const relationshipCard = screen.getByText('Jane Smith').closest('div')
    if (relationshipCard) {
      fireEvent.click(relationshipCard)
      
      expect(screen.getByText('Recent Events')).toBeInTheDocument()
      expect(screen.getByText('Mutual respect established')).toBeInTheDocument()
    }
  })

  it('calls onRelationshipClick when relationship is clicked', () => {
    render(<RelationshipDynamicsVisualization {...mockProps} />)
    
    const viewSelect = screen.getAllByRole('combobox')[1]
    fireEvent.click(viewSelect)
    const matrixOption = screen.getByText('Matrix')
    fireEvent.click(matrixOption)
    
    const relationshipCard = screen.getByText('Jane Smith').closest('div')
    if (relationshipCard) {
      fireEvent.click(relationshipCard)
      
      expect(mockProps.onRelationshipClick).toHaveBeenCalledWith('rel-1')
    }
  })

  it('displays trust and tension levels with progress bars', () => {
    render(<RelationshipDynamicsVisualization {...mockProps} />)
    
    const viewSelect = screen.getAllByRole('combobox')[1]
    fireEvent.click(viewSelect)
    const matrixOption = screen.getByText('Matrix')
    fireEvent.click(matrixOption)
    
    expect(screen.getByText('Trust')).toBeInTheDocument()
    expect(screen.getByText('Tension')).toBeInTheDocument()
    expect(screen.getByText('9/10')).toBeInTheDocument() // Latest trust level for John-Jane
    expect(screen.getByText('2/10')).toBeInTheDocument() // Latest tension level for John-Bob
  })

  it('shows trend indicators correctly', () => {
    render(<RelationshipDynamicsVisualization {...mockProps} />)
    
    const viewSelect = screen.getAllByRole('combobox')[1]
    fireEvent.click(viewSelect)
    const matrixOption = screen.getByText('Matrix')
    fireEvent.click(matrixOption)
    
    // Should have trend icons (up/down arrows) next to relationship names
    const trendIcons = screen.container.querySelectorAll('.lucide-arrow-up, .lucide-arrow-down, .lucide-minus')
    expect(trendIcons.length).toBeGreaterThan(0)
  })

  it('handles empty relationships list', () => {
    const emptyProps = {
      ...mockProps,
      character_relationships: []
    }
    
    render(<RelationshipDynamicsVisualization {...emptyProps} />)
    
    expect(screen.getByText('No Relationship Data')).toBeInTheDocument()
    expect(screen.getByText('No relationship dynamics found for the selected time range.')).toBeInTheDocument()
  })

  it('calculates network statistics correctly', () => {
    render(<RelationshipDynamicsVisualization {...mockProps} />)
    
    // Check that overview shows correct statistics
    expect(screen.getByText('Total Relationships')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    
    // Check average calculations are displayed
    expect(screen.getByText('Avg Trust')).toBeInTheDocument()
    expect(screen.getByText('Avg Tension')).toBeInTheDocument()
    
    // Check trend statistics
    expect(screen.getByText('Trends')).toBeInTheDocument()
  })

  it('displays relationship type badges correctly', () => {
    render(<RelationshipDynamicsVisualization {...mockProps} />)
    
    const viewSelect = screen.getAllByRole('combobox')[1]
    fireEvent.click(viewSelect)
    const matrixOption = screen.getByText('Matrix')
    fireEvent.click(matrixOption)
    
    expect(screen.getByText('friend')).toBeInTheDocument()
    expect(screen.getByText('rival')).toBeInTheDocument()
  })

  it('shows tooltip information on timeline graph points', () => {
    render(<RelationshipDynamicsVisualization {...mockProps} />)
    
    // Switch to timeline view and select a relationship
    const viewSelect = screen.getAllByRole('combobox')[1]
    fireEvent.click(viewSelect)
    const matrixOption = screen.getByText('Matrix')
    fireEvent.click(matrixOption)
    
    const relationshipCard = screen.getByText('Jane Smith').closest('div')
    if (relationshipCard) {
      fireEvent.click(relationshipCard)
      
      // Timeline should be rendered with graph points
      expect(screen.getByText('Relationship Dynamics Over Time')).toBeInTheDocument()
    }
  })

  it('filters out relationships with no dynamics in selected time range', () => {
    // Create a relationship with very old dynamics
    const oldRelationships = [{
      ...mockRelationships[0],
      dynamics: [{
        timestamp: '2022-01-01T00:00:00Z',
        trust_level: 5,
        tension_level: 5,
        description: 'Very old interaction'
      }]
    }]
    
    const propsWithOldData = {
      ...mockProps,
      character_relationships: oldRelationships
    }
    
    render(<RelationshipDynamicsVisualization {...propsWithOldData} />)
    
    // Set time range to 1 week, should filter out old relationships
    const timeRangeSelect = screen.getAllByRole('combobox')[0]
    fireEvent.click(timeRangeSelect)
    const oneWeekOption = screen.getByText('1 Week')
    fireEvent.click(oneWeekOption)
    
    expect(screen.getByText('No Relationship Data')).toBeInTheDocument()
  })

  it('displays relationship icons correctly for different types', () => {
    render(<RelationshipDynamicsVisualization {...mockProps} />)
    
    const viewSelect = screen.getAllByRole('combobox')[1]
    fireEvent.click(viewSelect)
    const matrixOption = screen.getByText('Matrix')
    fireEvent.click(matrixOption)
    
    // Should have heart icon for friend and flame icon for rival
    const icons = screen.container.querySelectorAll('.lucide-heart, .lucide-flame')
    expect(icons.length).toBeGreaterThan(0)
  })
}) 