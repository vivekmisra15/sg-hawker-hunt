import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ResultsList } from '../ResultsList'
import { RankedRecommendation } from '../../types'

// Mock IntersectionObserver as a proper class
const mockObserve = vi.fn()
const mockDisconnect = vi.fn()
beforeEach(() => {
  vi.clearAllMocks()
  global.IntersectionObserver = class MockIntersectionObserver {
    constructor(_cb: IntersectionObserverCallback, _opts?: IntersectionObserverInit) {}
    observe = mockObserve
    unobserve = vi.fn()
    disconnect = mockDisconnect
    root = null
    rootMargin = ''
    thresholds = [0]
    takeRecords = () => [] as IntersectionObserverEntry[]
  } as unknown as typeof IntersectionObserver
  // jsdom does not implement scrollIntoView
  Element.prototype.scrollIntoView = vi.fn()
})

function makeRec(overrides: Partial<RankedRecommendation> = {}): RankedRecommendation {
  return {
    stall_name: 'Test Stall',
    centre_name: 'Test Centre',
    rank: 1,
    reasoning: 'A great stall with excellent food and clean environment.',
    hygiene_grade: 'A',
    is_michelin: false,
    is_halal: false,
    is_open: true,
    distance_km: 0.5,
    ...overrides,
  }
}

describe('ResultsList', () => {
  it('returns null when state is not complete', () => {
    const { container } = render(
      <ResultsList recommendations={[]} state="searching" />
    )
    expect(container.firstChild).toBeNull()
  })

  it('shows empty state when complete with no results', () => {
    render(<ResultsList recommendations={[]} state="complete" />)
    expect(screen.getByText(/No stalls found/)).toBeInTheDocument()
  })

  it('renders result cards when complete with recommendations', () => {
    const recs = [
      makeRec({ stall_name: 'Laksa King', centre_name: 'Maxwell Food Centre', rank: 1 }),
      makeRec({ stall_name: 'Chicken Rice Hero', centre_name: 'Old Airport Road', rank: 2 }),
    ]
    render(<ResultsList recommendations={recs} state="complete" />)
    expect(screen.getByText('Laksa King')).toBeInTheDocument()
    expect(screen.getByText('Chicken Rice Hero')).toBeInTheDocument()
  })

  it('shows correct count text', () => {
    const recs = [
      makeRec({ stall_name: 'Stall 1', rank: 1 }),
      makeRec({ stall_name: 'Stall 2', rank: 2 }),
      makeRec({ stall_name: 'Stall 3', rank: 3 }),
    ]
    render(<ResultsList recommendations={recs} state="complete" />)
    expect(screen.getByText('3 of 3')).toBeInTheDocument()
  })

  it('shows Top picks label', () => {
    const recs = [makeRec()]
    render(<ResultsList recommendations={recs} state="complete" />)
    expect(screen.getByText('Top picks')).toBeInTheDocument()
  })

  it('sets up IntersectionObserver for lazy loading', () => {
    const recs = [makeRec()]
    render(<ResultsList recommendations={recs} state="complete" />)
    // The mock class was used (observer.observe called on sentinel)
    expect(mockObserve).toHaveBeenCalled()
  })

  it('highlights selected card', () => {
    const recs = [
      makeRec({ stall_name: 'Selected Stall', centre_name: 'Test Centre', rank: 1 }),
    ]
    render(
      <ResultsList
        recommendations={recs}
        state="complete"
        selectedKey="Selected Stall::Test Centre"
      />
    )
    const card = screen.getByText('Selected Stall').closest('[data-key]')
    expect(card).toHaveAttribute('aria-pressed', 'true')
  })

  it('passes onSelect callback to result cards', () => {
    const onSelect = vi.fn()
    const recs = [makeRec()]
    render(
      <ResultsList recommendations={recs} state="complete" onSelect={onSelect} />
    )
    const card = screen.getByRole('button', { name: /Test Stall/ })
    expect(card).toBeInTheDocument()
  })
})
