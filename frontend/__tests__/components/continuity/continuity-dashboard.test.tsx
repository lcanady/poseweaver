import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { ContinuityDashboard } from '@/components/continuity/continuity-dashboard'
import { ContinuityAlertsDisplay } from '@/components/continuity/continuity-alerts-display'
import { ContinuityFlagManager } from '@/components/continuity/continuity-flag-manager'
import { CharacterStateDisplay } from '@/components/continuity/character-state-display'
import { EnvironmentStateDisplay } from '@/components/continuity/environment-state-display'
import type { 
  ContinuityWarning, 
  ContinuityFlag, 
  CharacterState, 
  EnvironmentState 
} from '@/types/continuity'

// Mock the useToast hook
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}))

// Mock fetch
global.fetch = jest.fn()

const mockWarnings: ContinuityWarning[] = [
  {
    id: 'warning-1',
    type: 'character',
    severity: 'warning',
    title: 'Character Inconsistency',
    message: 'Character behavior seems inconsistent with established personality',
    suggestion: 'Review character profile and adjust behavior accordingly',
    action_required: true,
    dismissible: true,
    auto_dismiss_after: 30
  },
  {
    id: 'warning-2',
    type: 'environment',
    severity: 'error',
    title: 'Environmental Contradiction',
    message: 'Weather description conflicts with previously established conditions',
    action_required: true,
    dismissible: true
  }
]

const mockFlags: ContinuityFlag[] = [
  {
    id: 'flag-1',
    scene_id: 'scene-1',
    character_id: 'char-1',
    character_name: 'Alice',
    flag_type: 'character_consistency',
    severity: 'high',
    title: 'Character Voice Inconsistency',
    description: 'Character speech pattern differs from established voice',
    suggestion: 'Maintain consistent speech patterns',
    confidence_score: 85,
    created_at: '2024-01-01T10:00:00Z',
    updated_at: '2024-01-01T10:00:00Z',
    resolved: false
  },
  {
    id: 'flag-2',
    scene_id: 'scene-1',
    flag_type: 'environmental_contradiction',
    severity: 'medium',
    title: 'Lighting Contradiction',
    description: 'Lighting conditions mentioned conflict with time of day',
    confidence_score: 70,
    created_at: '2024-01-01T09:00:00Z',
    updated_at: '2024-01-01T09:00:00Z',
    resolved: true,
    resolved_at: '2024-01-01T11:00:00Z',
    resolution_notes: 'Adjusted to match established time of day'
  }
]

const mockCharacterStates: CharacterState[] = [
  {
    id: 'state-1',
    scene_id: 'scene-1',
    character_id: 'char-1',
    character_name: 'Alice',
    current_location: 'Library',
    physical_state: {
      health: 'Good',
      injuries: [],
      equipment: ['Book', 'Pen'],
      appearance: 'Wearing casual clothes'
    },
    emotional_state: {
      primary_emotion: 'Curious',
      secondary_emotions: ['Excited'],
      mood: 'Positive',
      stress_level: 20
    },
    mental_state: {
      alertness: 'Sharp',
      focus: 'Studying',
      memory_issues: []
    },
    relationships: [
      {
        character_name: 'Bob',
        relationship_type: 'Friend',
        relationship_status: 'Close friend',
        last_interaction: '2024-01-01T08:00:00Z'
      }
    ],
    plot_knowledge: {
      known_facts: ['Library has rare books'],
      secrets: ['Hidden passage behind bookshelf'],
      objectives: ['Find the ancient tome']
    },
    last_updated: '2024-01-01T10:00:00Z',
    updated_by: 'system',
    state_history: [
      {
        id: 'change-1',
        timestamp: '2024-01-01T10:00:00Z',
        change_type: 'location',
        before_value: 'Hallway',
        after_value: 'Library',
        automatic: true
      }
    ]
  }
]

const mockEnvironmentStates: EnvironmentState[] = [
  {
    id: 'env-1',
    scene_id: 'scene-1',
    location_name: 'Ancient Library',
    location_type: 'Indoor',
    physical_description: 'A vast library with towering bookshelves and dusty tomes',
    atmospheric_conditions: {
      lighting: 'Dim artificial lighting',
      weather: 'Clear',
      temperature: 'Cool',
      sounds: ['Rustling pages', 'Distant footsteps'],
      scents: ['Old books', 'Dust']
    },
    temporal_markers: {
      time_of_day: 'Afternoon',
      season: 'Autumn',
      special_events: []
    },
    interactive_elements: [
      {
        element_name: 'Ancient Reading Desk',
        description: 'A heavy wooden desk with intricate carvings',
        state: 'Available',
        interactive: true
      }
    ],
    occupants: ['Alice', 'Bob'],
    last_updated: '2024-01-01T10:00:00Z',
    environment_history: [
      {
        id: 'change-1',
        timestamp: '2024-01-01T10:00:00Z',
        change_type: 'occupancy',
        description: 'Alice entered the library',
        after_state: 'Alice present',
        automatic: true
      }
    ]
  }
]

describe('ContinuityDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, data: {} })
    })
  })

  it('renders the dashboard with all sections', async () => {
    render(
      <ContinuityDashboard
        scene_id="scene-1"
        scene_name="Test Scene"
        showRealTimeAlerts={true}
        showFlagManagement={true}
        showCharacterStates={true}
        showEnvironmentStates={true}
      />
    )

    expect(screen.getByText('Continuity Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Test Scene')).toBeInTheDocument()
    
    // Check for tab buttons
    expect(screen.getByText('Overview')).toBeInTheDocument()
    expect(screen.getByText(/Flags/)).toBeInTheDocument()
    expect(screen.getByText(/Characters/)).toBeInTheDocument()
    expect(screen.getByText(/Environment/)).toBeInTheDocument()
  })

  it('toggles settings panel', async () => {
    render(
      <ContinuityDashboard
        scene_id="scene-1"
        scene_name="Test Scene"
      />
    )

    const settingsButton = screen.getByRole('button', { name: /settings/i })
    fireEvent.click(settingsButton)

    await waitFor(() => {
      expect(screen.getByText('Auto Refresh')).toBeInTheDocument()
      expect(screen.getByText('Real-time Alerts')).toBeInTheDocument()
    })
  })
})

describe('ContinuityAlertsDisplay', () => {
  it('renders warnings correctly', () => {
    render(
      <ContinuityAlertsDisplay
        scene_id="scene-1"
        warnings={mockWarnings}
        onDismiss={jest.fn()}
        onAction={jest.fn()}
      />
    )

    expect(screen.getByText('Continuity Alerts')).toBeInTheDocument()
    expect(screen.getByText('Character Inconsistency')).toBeInTheDocument()
    expect(screen.getByText('Environmental Contradiction')).toBeInTheDocument()
  })

  it('handles warning dismissal', () => {
    const mockDismiss = jest.fn()
    render(
      <ContinuityAlertsDisplay
        scene_id="scene-1"
        warnings={mockWarnings}
        onDismiss={mockDismiss}
        onAction={jest.fn()}
      />
    )

    const dismissButtons = screen.getAllByRole('button', { name: /×/i })
    fireEvent.click(dismissButtons[0])

    expect(mockDismiss).toHaveBeenCalledWith('warning-1')
  })

  it('shows action buttons for warnings that require action', () => {
    render(
      <ContinuityAlertsDisplay
        scene_id="scene-1"
        warnings={mockWarnings}
        onDismiss={jest.fn()}
        onAction={jest.fn()}
      />
    )

    expect(screen.getAllByText('Resolve')).toHaveLength(2)
    expect(screen.getAllByText('Investigate')).toHaveLength(2)
  })
})

describe('ContinuityFlagManager', () => {
  it('renders flags correctly', () => {
    render(
      <ContinuityFlagManager
        scene_id="scene-1"
        flags={mockFlags}
        onResolve={jest.fn()}
        showResolved={true}
      />
    )

    expect(screen.getByText('Continuity Flags')).toBeInTheDocument()
    expect(screen.getByText('Character Voice Inconsistency')).toBeInTheDocument()
    expect(screen.getByText('Lighting Contradiction')).toBeInTheDocument()
  })

  it('filters flags by search query', () => {
    render(
      <ContinuityFlagManager
        scene_id="scene-1"
        flags={mockFlags}
        onResolve={jest.fn()}
        showFilters={true}
      />
    )

    const searchInput = screen.getByPlaceholderText('Search flags...')
    fireEvent.change(searchInput, { target: { value: 'voice' } })

    expect(screen.getByText('Character Voice Inconsistency')).toBeInTheDocument()
    expect(screen.queryByText('Lighting Contradiction')).not.toBeInTheDocument()
  })

  it('shows resolution dialog when resolve button is clicked', () => {
    render(
      <ContinuityFlagManager
        scene_id="scene-1"
        flags={mockFlags}
        onResolve={jest.fn()}
      />
    )

    const resolveButton = screen.getByRole('button', { name: /resolve/i })
    fireEvent.click(resolveButton)

    expect(screen.getByText('Resolve Continuity Flag')).toBeInTheDocument()
    expect(screen.getByText('Resolution Notes')).toBeInTheDocument()
  })
})

describe('CharacterStateDisplay', () => {
  it('renders character states correctly', () => {
    render(
      <CharacterStateDisplay
        character_states={mockCharacterStates}
        scene_id="scene-1"
        editable={true}
      />
    )

    expect(screen.getByText('Character States')).toBeInTheDocument()
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByText('Library')).toBeInTheDocument()
  })

  it('expands character details when clicked', () => {
    render(
      <CharacterStateDisplay
        character_states={mockCharacterStates}
        scene_id="scene-1"
        editable={true}
      />
    )

    const expandButton = screen.getByRole('button', { name: /chevron/i })
    fireEvent.click(expandButton)

    expect(screen.getByText('Physical State')).toBeInTheDocument()
    expect(screen.getByText('Emotional State')).toBeInTheDocument()
  })

  it('shows edit buttons when editable', () => {
    render(
      <CharacterStateDisplay
        character_states={mockCharacterStates}
        scene_id="scene-1"
        editable={true}
      />
    )

    const expandButton = screen.getByRole('button', { name: /chevron/i })
    fireEvent.click(expandButton)

    // Should show edit buttons for various fields
    const editButtons = screen.getAllByRole('button', { name: /edit/i })
    expect(editButtons.length).toBeGreaterThan(0)
  })
})

describe('EnvironmentStateDisplay', () => {
  it('renders environment states correctly', () => {
    render(
      <EnvironmentStateDisplay
        environment_states={mockEnvironmentStates}
        scene_id="scene-1"
        editable={true}
      />
    )

    expect(screen.getByText('Environment States')).toBeInTheDocument()
    expect(screen.getByText('Ancient Library')).toBeInTheDocument()
    expect(screen.getByText('Indoor')).toBeInTheDocument()
  })

  it('expands environment details when clicked', () => {
    render(
      <EnvironmentStateDisplay
        environment_states={mockEnvironmentStates}
        scene_id="scene-1"
        editable={true}
      />
    )

    const expandButton = screen.getByRole('button', { name: /chevron/i })
    fireEvent.click(expandButton)

    expect(screen.getByText('Description')).toBeInTheDocument()
    expect(screen.getByText('Conditions')).toBeInTheDocument()
  })

  it('shows interactive elements when enabled', () => {
    render(
      <EnvironmentStateDisplay
        environment_states={mockEnvironmentStates}
        scene_id="scene-1"
        showInteractiveElements={true}
      />
    )

    const expandButton = screen.getByRole('button', { name: /chevron/i })
    fireEvent.click(expandButton)

    const elementsTab = screen.getByText(/Elements/)
    fireEvent.click(elementsTab)

    expect(screen.getByText('Ancient Reading Desk')).toBeInTheDocument()
    expect(screen.getByText('Interactive')).toBeInTheDocument()
  })
}) 