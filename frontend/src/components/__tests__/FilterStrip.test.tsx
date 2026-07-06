import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import { FilterStrip, FilterKey } from '../FilterStrip'

function renderStrip(active: FilterKey[] = [], resultCount = 10, totalCount = 10) {
  const onToggle = vi.fn()
  const activeSet = new Set(active)
  render(
    <FilterStrip
      active={activeSet}
      onToggle={onToggle}
      resultCount={resultCount}
      totalCount={totalCount}
    />
  )
  return { onToggle }
}

describe('FilterStrip', () => {
  it('renders all five filter buttons', () => {
    renderStrip()
    expect(screen.getByRole('button', { name: 'Filter: Michelin' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Filter: Halal' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Filter: Open now' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Filter: Grade A' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Filter: Budget' })).toBeInTheDocument()
  })

  it('calls onToggle with correct key when clicked', async () => {
    const user = userEvent.setup()
    const { onToggle } = renderStrip()
    await user.click(screen.getByRole('button', { name: 'Filter: Michelin' }))
    expect(onToggle).toHaveBeenCalledWith('michelin')
  })

  it('sets aria-pressed true on active filters', () => {
    renderStrip(['halal', 'open'])
    expect(screen.getByRole('button', { name: 'Filter: Halal' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Filter: Open now' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Filter: Michelin' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('shows count indicator when filters are active', () => {
    renderStrip(['michelin'], 3, 10)
    expect(screen.getByText('3 of 10')).toBeInTheDocument()
  })

  it('hides count indicator when no filters are active', () => {
    renderStrip([], 10, 10)
    expect(screen.queryByText('10 of 10')).not.toBeInTheDocument()
  })
})
