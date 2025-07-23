import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { PlotThreadTrackingInterface } from '@/components/continuity/plot-thread-tracking-interface'
import { useToast } from '@/hooks/use-toast'

// Mock the toast hook
jest.mock('@/hooks/use-toast')
const mockToast = jest.fn()
;(useToast as jest.Mock).mockReturnValue({ toast: mockToast })

const mockPlotThreads = [
  {
    thread_id: 'thread-1',
    thread_name: 'The Ancient Artifact',
    thread_description: 'A mysterious ancient artifact has been discovered',
    thread_status: 'active' as const,
    importance: 'major' as const,
    created_timestamp: '2023-11-10T10:00:00Z',
    last_updated_timestamp: '2023-11-15T14:30:00Z',
    related_characters: [
      {
        character_id: 'char-1',
        character_name: 'John Doe',
        relevance: 'primary' as const
      }
    ],
    thread_elements: [
      {
        element_id: 'elem-1',
        thread_id: 'thread-1',
        element_type: 'clue' as const,
        element_name: 'Strange Markings',
        element_description: 'Unusual symbols found on the artifact',
        timestamp: '2023-11-12T09:15:00Z',
        status: 'introduced' as const,
        related_characters: []
      }
    ],
    scenes: [
      {
        scene_id: 'scene-1',
        scene_name: 'Discovery Scene',
        last_activity: '2023-11-15T14:30:00Z'
      }
    ]
  },
  {
    thread_id: 'thread-2',
    thread_name: 'Character Rivalry',
    thread_description: 'Growing tension between main characters',
    thread_status: 'paused' as const,
    importance: 'moderate' as const,
    created_timestamp: '2023-11-08T15:20:00Z',
    last_updated_timestamp: '2023-11-14T11:45:00Z',
    related_characters: [
      {
        character_id: 'char-1',
        character_name: 'John Doe', 
        relevance: 'primary' as const
      },
      {
        character_id: 'char-2',
        character_name: 'Jane Smith',
        relevance: 'primary' as const
      }
    ],
    thread_elements: [],
    scenes: []
  }
]

const mockProps = {
  scene_id: 'scene-1',
  threads: mockPlotThreads,
  onThreadClick: jest.fn(),
  onElementClick: jest.fn(),
  onCreateThread: jest.fn(),
  onUpdateThread: jest.fn(),
  onDeleteThread: jest.fn(),
  onCreateElement: jest.fn(),
  onUpdateElement: jest.fn(),
  onDeleteElement: jest.fn(),
  compact: false,
  editable: true
}

describe('PlotThreadTrackingInterface', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders component with thread count', () => {
    render(<PlotThreadTrackingInterface {...mockProps} />)
    
    expect(screen.getByText('Plot Thread Tracking')).toBeInTheDocument()
    expect(screen.getByText('2 threads')).toBeInTheDocument()
  })

  it('displays all plot threads with correct information', () => {
    render(<PlotThreadTrackingInterface {...mockProps} />)
    
    expect(screen.getByText('The Ancient Artifact')).toBeInTheDocument()
    expect(screen.getByText('Character Rivalry')).toBeInTheDocument()
    expect(screen.getByText('active')).toBeInTheDocument()
    expect(screen.getByText('paused')).toBeInTheDocument()
    expect(screen.getByText('major')).toBeInTheDocument()
    expect(screen.getByText('moderate')).toBeInTheDocument()
  })

  it('opens create thread dialog when New Thread button is clicked', () => {
    render(<PlotThreadTrackingInterface {...mockProps} />)
    
    const newThreadButton = screen.getByText('New Thread')
    fireEvent.click(newThreadButton)
    
    expect(screen.getByText('Create Plot Thread')).toBeInTheDocument()
  })

  it('filters threads by search query', () => {
    render(<PlotThreadTrackingInterface {...mockProps} />)
    
    const searchInput = screen.getByPlaceholderText('Search threads...')
    fireEvent.change(searchInput, { target: { value: 'Artifact' } })
    
    expect(screen.getByText('The Ancient Artifact')).toBeInTheDocument()
    expect(screen.queryByText('Character Rivalry')).not.toBeInTheDocument()
  })

  it('filters threads by status', () => {
    render(<PlotThreadTrackingInterface {...mockProps} />)
    
    const statusSelect = screen.getAllByRole('combobox')[1] // Second select is status
    fireEvent.click(statusSelect)
    
    const activeOption = screen.getByText('Active')
    fireEvent.click(activeOption)
    
    expect(screen.getByText('The Ancient Artifact')).toBeInTheDocument()
    expect(screen.queryByText('Character Rivalry')).not.toBeInTheDocument()
  })

  it('filters threads by importance', () => {
    render(<PlotThreadTrackingInterface {...mockProps} />)
    
    const importanceSelect = screen.getAllByRole('combobox')[2] // Third select is importance
    fireEvent.click(importanceSelect)
    
    const majorOption = screen.getByText('Major')
    fireEvent.click(majorOption)
    
    expect(screen.getByText('The Ancient Artifact')).toBeInTheDocument()
    expect(screen.queryByText('Character Rivalry')).not.toBeInTheDocument()
  })

  it('expands thread to show elements, characters, and scenes', () => {
    render(<PlotThreadTrackingInterface {...mockProps} />)
    
    const expandButtons = screen.getAllByRole('button')
    const expandButton = expandButtons.find(button => 
      button.querySelector('svg')?.classList.contains('lucide-chevron-down')
    )
    
    if (expandButton) {
      fireEvent.click(expandButton)
      
      expect(screen.getByText('Elements (1)')).toBeInTheDocument()
      expect(screen.getByText('Characters (1)')).toBeInTheDocument()
      expect(screen.getByText('Scenes (1)')).toBeInTheDocument()
    }
  })

  it('calls onThreadClick when thread name is clicked', () => {
    render(<PlotThreadTrackingInterface {...mockProps} />)
    
    const threadButton = screen.getByRole('button', { name: 'The Ancient Artifact' })
    fireEvent.click(threadButton)
    
    expect(mockProps.onThreadClick).toHaveBeenCalledWith(
      expect.objectContaining({ thread_id: 'thread-1' })
    )
  })

  it('opens edit thread dialog when edit button is clicked', () => {
    render(<PlotThreadTrackingInterface {...mockProps} />)
    
    const editButtons = screen.getAllByRole('button')
    const editButton = editButtons.find(button => 
      button.querySelector('svg')?.classList.contains('lucide-edit')
    )
    
    if (editButton) {
      fireEvent.click(editButton)
      expect(screen.getByText('Edit Plot Thread')).toBeInTheDocument()
    }
  })

  it('creates new thread when form is submitted', async () => {
    render(<PlotThreadTrackingInterface {...mockProps} />)
    
    const newThreadButton = screen.getByText('New Thread')
    fireEvent.click(newThreadButton)
    
    const nameInput = screen.getByPlaceholderText('Enter thread name...')
    fireEvent.change(nameInput, { target: { value: 'New Plot Thread' } })
    
    const descriptionInput = screen.getByPlaceholderText('Describe this plot thread...')
    fireEvent.change(descriptionInput, { target: { value: 'Test description' } })
    
    const createButton = screen.getByRole('button', { name: /Create/ })
    fireEvent.click(createButton)
    
    await waitFor(() => {
      expect(mockProps.onCreateThread).toHaveBeenCalled()
    })

    expect(mockToast).toHaveBeenCalledWith({
      title: 'Thread Created',
      description: 'Plot thread "New Plot Thread" has been created.'
    })
  })

  it('shows delete confirmation dialog', () => {
    render(<PlotThreadTrackingInterface {...mockProps} />)
    
    const deleteButtons = screen.getAllByRole('button')
    const deleteButton = deleteButtons.find(button => 
      button.querySelector('svg')?.classList.contains('lucide-trash-2')
    )
    
    if (deleteButton) {
      fireEvent.click(deleteButton)
      expect(screen.getByText('Delete Plot Thread')).toBeInTheDocument()
      expect(screen.getByText(/Are you sure you want to delete/)).toBeInTheDocument()
    }
  })

  it('calls onDeleteThread when delete is confirmed', () => {
    render(<PlotThreadTrackingInterface {...mockProps} />)
    
    const deleteButtons = screen.getAllByRole('button')
    const deleteButton = deleteButtons.find(button => 
      button.querySelector('svg')?.classList.contains('lucide-trash-2')
    )
    
    if (deleteButton) {
      fireEvent.click(deleteButton)
      
      const confirmButton = screen.getByText('Delete')
      fireEvent.click(confirmButton)
      
      expect(mockProps.onDeleteThread).toHaveBeenCalledWith('thread-1')
    }
  })

  it('handles bulk selection and deletion', () => {
    render(<PlotThreadTrackingInterface {...mockProps} />)
    
    const checkboxes = screen.getAllByRole('checkbox')
    fireEvent.click(checkboxes[0])
    
    expect(screen.getByText(/Delete \(1\)/)).toBeInTheDocument()
  })

  it('creates plot element when form is submitted', async () => {
    render(<PlotThreadTrackingInterface {...mockProps} />)
    
    // First expand a thread
    const expandButtons = screen.getAllByRole('button')
    const expandButton = expandButtons.find(button => 
      button.querySelector('svg')?.classList.contains('lucide-chevron-down')
    )
    
    if (expandButton) {
      fireEvent.click(expandButton)
      
      const addElementButton = screen.getByText('Add Element')
      fireEvent.click(addElementButton)
      
      expect(screen.getByText('Create Plot Element')).toBeInTheDocument()
      
      const elementNameInput = screen.getByPlaceholderText('Enter element name...')
      fireEvent.change(elementNameInput, { target: { value: 'New Element' } })
      
      const createElementButton = screen.getByRole('button', { name: /Create/ })
      fireEvent.click(createElementButton)
      
      await waitFor(() => {
        expect(mockProps.onCreateElement).toHaveBeenCalledWith('thread-1')
      })
    }
  })

  it('validates thread name input before submission', () => {
    render(<PlotThreadTrackingInterface {...mockProps} />)
    
    const newThreadButton = screen.getByText('New Thread')
    fireEvent.click(newThreadButton)
    
    const createButton = screen.getByRole('button', { name: /Create/ })
    fireEvent.click(createButton)
    
    expect(mockToast).toHaveBeenCalledWith({
      title: 'Name Required',
      description: 'Please provide a thread name.',
      variant: 'destructive'
    })
  })

  it('shows empty state when no threads exist', () => {
    const emptyProps = { ...mockProps, threads: [] }
    render(<PlotThreadTrackingInterface {...emptyProps} />)
    
    expect(screen.getByText('No Plot Threads')).toBeInTheDocument()
    expect(screen.getByText('Start tracking plot threads to maintain story consistency.')).toBeInTheDocument()
    expect(screen.getByText('Create First Thread')).toBeInTheDocument()
  })

  it('shows filtered empty state when search returns no results', () => {
    render(<PlotThreadTrackingInterface {...mockProps} />)
    
    const searchInput = screen.getByPlaceholderText('Search threads...')
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } })
    
    expect(screen.getByText('No threads match your current filters.')).toBeInTheDocument()
  })

  it('disables edit functionality when editable is false', () => {
    const readOnlyProps = { ...mockProps, editable: false }
    render(<PlotThreadTrackingInterface {...readOnlyProps} />)
    
    expect(screen.queryByText('New Thread')).not.toBeInTheDocument()
  })
}) 