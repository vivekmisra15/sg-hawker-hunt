import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { SearchBar } from '../SearchBar'

// Mock useGeolocation to avoid navigator.geolocation setup complexity
vi.mock('../../hooks/useGeolocation', () => ({
  useGeolocation: () => ({
    lat: null,
    lng: null,
    error: null,
    loading: false,
    request: vi.fn(),
    clear: vi.fn(),
  }),
}))

describe('SearchBar', () => {
  let onSearch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    onSearch = vi.fn()
  })

  it('renders the search input with correct aria-label', () => {
    render(<SearchBar onSearch={onSearch} isSearching={false} />)
    expect(screen.getByLabelText('Search for hawker food in Singapore')).toBeInTheDocument()
  })

  it('renders all four example chips', () => {
    render(<SearchBar onSearch={onSearch} isSearching={false} />)
    const group = screen.getByRole('group', { name: 'Example searches' })
    expect(group).toBeInTheDocument()
    // 4 chip buttons inside the group
    const chips = group.querySelectorAll('button')
    expect(chips).toHaveLength(4)
  })

  it('fills input when chip is clicked', async () => {
    const user = userEvent.setup()
    render(<SearchBar onSearch={onSearch} isSearching={false} />)
    await user.click(screen.getByLabelText(/Try search: Chicken rice/))
    const input = screen.getByLabelText('Search for hawker food in Singapore') as HTMLInputElement
    expect(input.value).toBe('Chicken rice near me')
  })

  it('calls onSearch when Enter is pressed with non-empty query', async () => {
    const user = userEvent.setup()
    render(<SearchBar onSearch={onSearch} isSearching={false} />)
    const input = screen.getByLabelText('Search for hawker food in Singapore')
    await user.type(input, 'laksa near Toa Payoh')
    await user.keyboard('{Enter}')
    expect(onSearch).toHaveBeenCalledWith('laksa near Toa Payoh', undefined, undefined)
  })

  it('does not call onSearch with empty query', async () => {
    const user = userEvent.setup()
    render(<SearchBar onSearch={onSearch} isSearching={false} />)
    const input = screen.getByLabelText('Search for hawker food in Singapore')
    await user.click(input)
    await user.keyboard('{Enter}')
    expect(onSearch).not.toHaveBeenCalled()
  })

  it('disables input while searching', () => {
    render(<SearchBar onSearch={onSearch} isSearching={true} />)
    const input = screen.getByLabelText('Search for hawker food in Singapore')
    expect(input).toBeDisabled()
  })

  it('shows searching label on submit button while searching', () => {
    render(<SearchBar onSearch={onSearch} isSearching={true} />)
    expect(screen.getByLabelText('Searching...')).toBeInTheDocument()
  })

  it('shows search label on submit button when idle', () => {
    render(<SearchBar onSearch={onSearch} isSearching={false} />)
    expect(screen.getByLabelText('Search')).toBeInTheDocument()
  })

  it('calls onSearch when submit button is clicked', async () => {
    const user = userEvent.setup()
    render(<SearchBar onSearch={onSearch} isSearching={false} />)
    const input = screen.getByLabelText('Search for hawker food in Singapore')
    await user.type(input, 'chicken rice')
    await user.click(screen.getByLabelText('Search'))
    expect(onSearch).toHaveBeenCalledWith('chicken rice', undefined, undefined)
  })

  it('renders location button with default aria-label', () => {
    render(<SearchBar onSearch={onSearch} isSearching={false} />)
    expect(screen.getByLabelText('Use my location')).toBeInTheDocument()
  })
})
