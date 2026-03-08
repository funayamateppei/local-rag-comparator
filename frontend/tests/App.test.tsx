import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '../src/App'

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    expect(document.body).toBeTruthy()
  })

  it('renders the heading', () => {
    render(<App />)
    expect(screen.getByText('Vite + React')).toBeInTheDocument()
  })

  it('renders the count button', () => {
    render(<App />)
    expect(screen.getByText('count is 0')).toBeInTheDocument()
  })
})
