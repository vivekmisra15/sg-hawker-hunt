import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { StatusBadge } from '../StatusBadge'

describe('StatusBadge', () => {
  it('renders Grade A with success styling', () => {
    render(<StatusBadge type="grade" value="A" />)
    const badge = screen.getByText('Grade A')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toContain('text-success')
  })

  it('renders Grade B with warning styling', () => {
    render(<StatusBadge type="grade" value="B" />)
    expect(screen.getByText('Grade B')).toBeInTheDocument()
  })

  it('renders Grade C with danger styling', () => {
    render(<StatusBadge type="grade" value="C" />)
    const badge = screen.getByText('Grade C')
    expect(badge.className).toContain('text-danger')
  })

  it('renders UNKNOWN as neutral dash', () => {
    render(<StatusBadge type="grade" value="UNKNOWN" />)
    expect(screen.getByText('Grade —')).toBeInTheDocument()
  })

  it('renders missing grade with question mark', () => {
    render(<StatusBadge type="grade" />)
    expect(screen.getByText('Grade ?')).toBeInTheDocument()
  })

  it('renders Michelin Bib Gourmand badge', () => {
    render(<StatusBadge type="michelin" />)
    expect(screen.getByText(/Bib Gourmand/)).toBeInTheDocument()
  })

  it('renders Halal badge', () => {
    render(<StatusBadge type="halal" />)
    expect(screen.getByText(/Halal/)).toBeInTheDocument()
  })

  it('renders Open now with pulsing dot', () => {
    render(<StatusBadge type="open" />)
    expect(screen.getByText('Open now')).toBeInTheDocument()
  })

  it('renders Closed badge', () => {
    render(<StatusBadge type="closed" />)
    expect(screen.getByText('Closed')).toBeInTheDocument()
  })

  it('renders busy crowd badge', () => {
    render(<StatusBadge type="crowd" value="busy" />)
    expect(screen.getByText('Busy now')).toBeInTheDocument()
  })

  it('renders quiet crowd badge', () => {
    render(<StatusBadge type="crowd" value="quiet" />)
    expect(screen.getByText('Quiet')).toBeInTheDocument()
  })

  it('renders cheap price badge', () => {
    render(<StatusBadge type="price" value="cheap" />)
    expect(screen.getByText('$ Under $6')).toBeInTheDocument()
  })

  it('renders moderate price badge', () => {
    render(<StatusBadge type="price" value="moderate" />)
    expect(screen.getByText('$$ Moderate')).toBeInTheDocument()
  })

  it('returns null for unknown price value', () => {
    const { container } = render(<StatusBadge type="price" value="unknown" />)
    expect(container.firstChild).toBeNull()
  })
})
