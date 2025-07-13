import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  test('renders MUSH Pose Editor title', () => {
    render(<App />)
    const titleElement = screen.getByText(/MUSH Pose Editor/i)
    expect(titleElement).toBeInTheDocument()
  })

  test('renders coming soon message', () => {
    render(<App />)
    const comingSoonElement = screen.getByText(/Coming Soon/i)
    expect(comingSoonElement).toBeInTheDocument()
  })

  test('renders description text', () => {
    render(<App />)
    const descriptionElement = screen.getByText(/AI-powered writing assistant for roleplayers/i)
    expect(descriptionElement).toBeInTheDocument()
  })
}) 