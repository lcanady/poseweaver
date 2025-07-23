/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SceneCreationForm } from '@/components/scene-management/scene-creation-form'
import type { SceneCreationData } from '@/types/scene'

// Mock the API calls
global.fetch = jest.fn()
global.localStorage = {
  getItem: jest.fn(() => 'mock-token'),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
} as any

// Mock the character API response
const mockCharacters = [
  { id: '1', name: 'Character 1', description: 'Test character 1' },
  { id: '2', name: 'Character 2', description: 'Test character 2' }
]

describe('SceneCreationForm', () => {
  const mockOnSubmit = jest.fn()
  const mockOnCancel = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    ;(fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('/api/characters')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ data: mockCharacters })
        })
      }
      return Promise.reject(new Error('Unknown URL'))
    })
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('renders the form with basic fields', () => {
    render(<SceneCreationForm onSubmit={mockOnSubmit} />)
    
    expect(screen.getByText('Create New Scene')).toBeInTheDocument()
    expect(screen.getByLabelText('Scene Name')).toBeInTheDocument()
    expect(screen.getByLabelText('Description')).toBeInTheDocument()
    expect(screen.getByText('Basic Info')).toBeInTheDocument()
    expect(screen.getByText('Participants')).toBeInTheDocument()
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('shows edit mode when isEditing is true', () => {
    render(<SceneCreationForm onSubmit={mockOnSubmit} isEditing={true} />)
    
    expect(screen.getByText('Edit Scene')).toBeInTheDocument()
    expect(screen.getByText('Update Scene')).toBeInTheDocument()
  })

  it('validates required fields', async () => {
    const user = userEvent.setup()
    render(<SceneCreationForm onSubmit={mockOnSubmit} />)
    
    const submitButton = screen.getByText('Create Scene')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText('Scene name is required')).toBeInTheDocument()
    })
  })

  it('validates minimum description length', async () => {
    const user = userEvent.setup()
    render(<SceneCreationForm onSubmit={mockOnSubmit} />)
    
    const nameInput = screen.getByLabelText('Scene Name')
    const descriptionInput = screen.getByLabelText('Description')
    
    await user.type(nameInput, 'Test Scene')
    await user.type(descriptionInput, 'Short')
    
    const submitButton = screen.getByText('Create Scene')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText('Scene description must be at least 10 characters')).toBeInTheDocument()
    })
  })

  it('validates maximum field lengths', async () => {
    const user = userEvent.setup()
    render(<SceneCreationForm onSubmit={mockOnSubmit} />)
    
    const nameInput = screen.getByLabelText('Scene Name')
    const longName = 'a'.repeat(101)
    
    await user.type(nameInput, longName)
    
    const submitButton = screen.getByText('Create Scene')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText('Scene name must be 100 characters or less')).toBeInTheDocument()
    })
  })

  it('adds and removes tags', async () => {
    const user = userEvent.setup()
    render(<SceneCreationForm onSubmit={mockOnSubmit} />)
    
    const tagInput = screen.getByPlaceholderText('Add tags...')
    const addButton = screen.getByRole('button', { name: '' }) // Plus icon button
    
    await user.type(tagInput, 'fantasy')
    await user.click(addButton)
    
    expect(screen.getByText('fantasy')).toBeInTheDocument()
    
    // Remove tag
    const removeButton = screen.getByRole('button', { name: '' }) // X icon button in tag
    await user.click(removeButton)
    
    expect(screen.queryByText('fantasy')).not.toBeInTheDocument()
  })

  it('adds tag on Enter key press', async () => {
    const user = userEvent.setup()
    render(<SceneCreationForm onSubmit={mockOnSubmit} />)
    
    const tagInput = screen.getByPlaceholderText('Add tags...')
    
    await user.type(tagInput, 'adventure')
    await user.keyboard('{Enter}')
    
    expect(screen.getByText('adventure')).toBeInTheDocument()
  })

  it('loads and displays characters for selection', async () => {
    const user = userEvent.setup()
    render(<SceneCreationForm onSubmit={mockOnSubmit} />)
    
    // Switch to participants tab
    await user.click(screen.getByText('Participants'))
    
    // Open character selection dialog
    await user.click(screen.getByText('Add Character'))
    
    await waitFor(() => {
      expect(screen.getByText('Character 1')).toBeInTheDocument()
      expect(screen.getByText('Character 2')).toBeInTheDocument()
    })
  })

  it('adds and removes participants', async () => {
    const user = userEvent.setup()
    render(<SceneCreationForm onSubmit={mockOnSubmit} />)
    
    // Switch to participants tab
    await user.click(screen.getByText('Participants'))
    
    // Open character selection dialog
    await user.click(screen.getByText('Add Character'))
    
    await waitFor(() => {
      expect(screen.getByText('Character 1')).toBeInTheDocument()
    })
    
    // Add character
    await user.click(screen.getByText('Character 1'))
    
    await waitFor(() => {
      expect(screen.getByText('Character 1')).toBeInTheDocument()
    })
    
    // Remove character
    const removeButton = screen.getByRole('button', { name: '' }) // X icon button
    await user.click(removeButton)
    
    expect(screen.queryByText('Character 1')).not.toBeInTheDocument()
  })

  it('handles scene type selection', async () => {
    const user = userEvent.setup()
    render(<SceneCreationForm onSubmit={mockOnSubmit} />)
    
    // Switch to settings tab
    await user.click(screen.getByText('Settings'))
    
    // Change scene type
    await user.click(screen.getByText('Select scene type'))
    await user.click(screen.getByText('One-shot'))
    
    expect(screen.getByText('One-shot')).toBeInTheDocument()
  })

  it('handles privacy level selection', async () => {
    const user = userEvent.setup()
    render(<SceneCreationForm onSubmit={mockOnSubmit} />)
    
    // Switch to settings tab
    await user.click(screen.getByText('Settings'))
    
    // Change privacy level
    await user.click(screen.getByText('Select privacy level'))
    await user.click(screen.getByText('Public'))
    
    expect(screen.getByText('Public')).toBeInTheDocument()
  })

  it('handles checkbox options', async () => {
    const user = userEvent.setup()
    render(<SceneCreationForm onSubmit={mockOnSubmit} />)
    
    // Switch to settings tab
    await user.click(screen.getByText('Settings'))
    
    const checkbox = screen.getByRole('checkbox')
    await user.click(checkbox)
    
    expect(checkbox).toBeChecked()
  })

  it('calls onSubmit with correct data', async () => {
    const user = userEvent.setup()
    render(<SceneCreationForm onSubmit={mockOnSubmit} />)
    
    // Fill required fields
    await user.type(screen.getByLabelText('Scene Name'), 'Test Scene')
    await user.type(screen.getByLabelText('Description'), 'This is a test scene description')
    
    // Submit form
    await user.click(screen.getByText('Create Scene'))
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        name: 'Test Scene',
        description: 'This is a test scene description',
        tags: [],
        participants: [],
        initial_setting: '',
        scene_type: 'ongoing',
        privacy_level: 'private',
        allow_new_participants: false
      })
    })
  })

  it('populates form with initial data', () => {
    const initialData = {
      name: 'Existing Scene',
      description: 'Existing description',
      tags: ['fantasy', 'adventure'],
      participants: [{ character_id: '1', character_name: 'Character 1' }],
      scene_type: 'oneshot' as const,
      privacy_level: 'public' as const,
      allow_new_participants: true
    }
    
    render(<SceneCreationForm onSubmit={mockOnSubmit} initialData={initialData} />)
    
    expect(screen.getByDisplayValue('Existing Scene')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Existing description')).toBeInTheDocument()
    expect(screen.getByText('fantasy')).toBeInTheDocument()
    expect(screen.getByText('adventure')).toBeInTheDocument()
  })

  it('calls onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup()
    render(<SceneCreationForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)
    
    await user.click(screen.getByText('Cancel'))
    
    expect(mockOnCancel).toHaveBeenCalled()
  })

  it('shows loading state when loading prop is true', () => {
    render(<SceneCreationForm onSubmit={mockOnSubmit} loading={true} />)
    
    const submitButton = screen.getByText('Create Scene')
    expect(submitButton).toBeDisabled()
  })

  it('displays error message when error prop is provided', () => {
    const errorMessage = 'Something went wrong'
    render(<SceneCreationForm onSubmit={mockOnSubmit} error={errorMessage} />)
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument()
  })

  it('prevents duplicate tags', async () => {
    const user = userEvent.setup()
    render(<SceneCreationForm onSubmit={mockOnSubmit} />)
    
    const tagInput = screen.getByPlaceholderText('Add tags...')
    const addButton = screen.getByRole('button', { name: '' }) // Plus icon button
    
    // Add first tag
    await user.type(tagInput, 'fantasy')
    await user.click(addButton)
    
    // Try to add same tag again
    await user.type(tagInput, 'fantasy')
    await user.click(addButton)
    
    // Should only have one instance of the tag
    const fantasyTags = screen.getAllByText('fantasy')
    expect(fantasyTags).toHaveLength(1)
  })

  it('prevents duplicate participants', async () => {
    const user = userEvent.setup()
    render(<SceneCreationForm onSubmit={mockOnSubmit} />)
    
    // Switch to participants tab
    await user.click(screen.getByText('Participants'))
    
    // Add character
    await user.click(screen.getByText('Add Character'))
    
    await waitFor(() => {
      const character1Button = screen.getByText('Character 1')
      expect(character1Button).toBeInTheDocument()
    })
    
    await user.click(screen.getByText('Character 1'))
    
    // Try to add same character again
    await user.click(screen.getByText('Add Character'))
    
    await waitFor(() => {
      const character1Button = screen.getByText('Character 1')
      expect(character1Button).toBeDisabled()
    })
  })

  it('handles character loading error gracefully', async () => {
    ;(fetch as jest.Mock).mockImplementation(() => 
      Promise.reject(new Error('Failed to load characters'))
    )
    
    const user = userEvent.setup()
    render(<SceneCreationForm onSubmit={mockOnSubmit} />)
    
    await user.click(screen.getByText('Participants'))
    await user.click(screen.getByText('Add Character'))
    
    // Should still show the dialog even if characters fail to load
    await waitFor(() => {
      expect(screen.getByText('Select Character')).toBeInTheDocument()
    })
  })

  it('handles form submission error gracefully', async () => {
    const mockOnSubmitError = jest.fn().mockRejectedValue(new Error('Submission failed'))
    const user = userEvent.setup()
    
    render(<SceneCreationForm onSubmit={mockOnSubmitError} />)
    
    await user.type(screen.getByLabelText('Scene Name'), 'Test Scene')
    await user.type(screen.getByLabelText('Description'), 'This is a test scene description')
    
    await user.click(screen.getByText('Create Scene'))
    
    await waitFor(() => {
      expect(mockOnSubmitError).toHaveBeenCalled()
    })
  })

  it('clears tag input after adding tag', async () => {
    const user = userEvent.setup()
    render(<SceneCreationForm onSubmit={mockOnSubmit} />)
    
    const tagInput = screen.getByPlaceholderText('Add tags...')
    const addButton = screen.getByRole('button', { name: '' }) // Plus icon button
    
    await user.type(tagInput, 'fantasy')
    await user.click(addButton)
    
    expect(tagInput).toHaveValue('')
  })

  it('validates all form fields together', async () => {
    const user = userEvent.setup()
    render(<SceneCreationForm onSubmit={mockOnSubmit} />)
    
    // Fill out complete form
    await user.type(screen.getByLabelText('Scene Name'), 'Complete Test Scene')
    await user.type(screen.getByLabelText('Description'), 'This is a complete test scene description with enough characters')
    await user.type(screen.getByLabelText('Initial Setting'), 'A mystical forest clearing')
    
    // Add tags
    const tagInput = screen.getByPlaceholderText('Add tags...')
    await user.type(tagInput, 'fantasy')
    await user.keyboard('{Enter}')
    await user.type(tagInput, 'adventure')
    await user.keyboard('{Enter}')
    
    // Switch to settings and configure
    await user.click(screen.getByText('Settings'))
    await user.click(screen.getByText('Select scene type'))
    await user.click(screen.getByText('Campaign'))
    
    // Submit form
    await user.click(screen.getByText('Create Scene'))
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        name: 'Complete Test Scene',
        description: 'This is a complete test scene description with enough characters',
        initial_setting: 'A mystical forest clearing',
        tags: ['fantasy', 'adventure'],
        participants: [],
        scene_type: 'campaign',
        privacy_level: 'private',
        allow_new_participants: false
      })
    })
  })
}) 