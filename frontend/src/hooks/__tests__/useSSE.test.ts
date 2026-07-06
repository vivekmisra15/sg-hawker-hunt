import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useSSE } from '../useSSE'

// Mock the api module
vi.mock('../../lib/api', () => ({
  createSearchStream: vi.fn(),
}))

import { createSearchStream } from '../../lib/api'

const mockCreateSearchStream = vi.mocked(createSearchStream)

describe('useSSE', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('starts in idle state with empty results', () => {
    const { result } = renderHook(() => useSSE())
    expect(result.current.state).toBe('idle')
    expect(result.current.traces).toEqual([])
    expect(result.current.results).toEqual([])
    expect(result.current.error).toBeNull()
  })

  it('transitions to searching state on search', () => {
    const cancelFn = vi.fn()
    mockCreateSearchStream.mockReturnValue(cancelFn)

    const { result } = renderHook(() => useSSE())
    act(() => { result.current.search('laksa') })
    expect(result.current.state).toBe('searching')
  })

  it('passes query and coordinates to createSearchStream', () => {
    const cancelFn = vi.fn()
    mockCreateSearchStream.mockReturnValue(cancelFn)

    const { result } = renderHook(() => useSSE())
    act(() => { result.current.search('chicken rice', 1.35, 103.82) })
    expect(mockCreateSearchStream).toHaveBeenCalledWith(
      'chicken rice', 1.35, 103.82,
      expect.any(Function),
      expect.any(Function),
      expect.any(Function),
    )
  })

  it('adds traces on agent_update events', () => {
    mockCreateSearchStream.mockImplementation(
      (_q, _lat, _lng, onEvent) => {
        onEvent({
          type: 'agent_update',
          agent: 'hygiene',
          message: 'Checking grades...',
        })
        return vi.fn()
      }
    )

    const { result } = renderHook(() => useSSE())
    act(() => { result.current.search('laksa') })
    expect(result.current.traces).toHaveLength(1)
    expect(result.current.traces[0].agent).toBe('hygiene')
    expect(result.current.traces[0].message).toBe('Checking grades...')
  })

  it('sets results and completes on result event', () => {
    const recommendations = [
      { stall_name: 'Test Stall', centre_name: 'Test Centre', rank: 1, reasoning: 'Good', hygiene_grade: 'A', is_michelin: false, is_halal: false, is_open: true, distance_km: 0.5 },
    ]

    mockCreateSearchStream.mockImplementation(
      (_q, _lat, _lng, onEvent) => {
        onEvent({
          type: 'result',
          data: { recommendations },
        })
        return vi.fn()
      }
    )

    const { result } = renderHook(() => useSSE())
    act(() => { result.current.search('laksa') })
    expect(result.current.results).toHaveLength(1)
    expect(result.current.results[0].stall_name).toBe('Test Stall')
    expect(result.current.state).toBe('complete')
  })

  it('sets error state on error event', () => {
    mockCreateSearchStream.mockImplementation(
      (_q, _lat, _lng, onEvent) => {
        onEvent({
          type: 'error',
          message: 'API key missing',
        })
        return vi.fn()
      }
    )

    const { result } = renderHook(() => useSSE())
    act(() => { result.current.search('laksa') })
    expect(result.current.state).toBe('error')
    expect(result.current.error).toBe('API key missing')
  })

  it('sets error state on stream error callback', () => {
    mockCreateSearchStream.mockImplementation(
      (_q, _lat, _lng, _onEvent, onError) => {
        onError('Network failure')
        return vi.fn()
      }
    )

    const { result } = renderHook(() => useSSE())
    act(() => { result.current.search('laksa') })
    expect(result.current.state).toBe('error')
    expect(result.current.error).toBe('Network failure')
  })

  it('transitions to complete on onComplete if still searching', () => {
    mockCreateSearchStream.mockImplementation(
      (_q, _lat, _lng, _onEvent, _onError, onComplete) => {
        onComplete()
        return vi.fn()
      }
    )

    const { result } = renderHook(() => useSSE())
    act(() => { result.current.search('laksa') })
    expect(result.current.state).toBe('complete')
  })

  it('resets all state on reset()', () => {
    const cancelFn = vi.fn()
    mockCreateSearchStream.mockImplementation(
      (_q, _lat, _lng, onEvent) => {
        onEvent({
          type: 'agent_update',
          agent: 'orchestrator',
          message: 'Parsing query...',
        })
        return cancelFn
      }
    )

    const { result } = renderHook(() => useSSE())
    act(() => { result.current.search('laksa') })
    expect(result.current.traces).toHaveLength(1)

    act(() => { result.current.reset() })
    expect(result.current.state).toBe('idle')
    expect(result.current.traces).toEqual([])
    expect(result.current.results).toEqual([])
    expect(result.current.error).toBeNull()
    expect(cancelFn).toHaveBeenCalled()
  })

  it('cancels previous search when starting a new one', () => {
    const cancel1 = vi.fn()
    const cancel2 = vi.fn()
    mockCreateSearchStream
      .mockReturnValueOnce(cancel1)
      .mockReturnValueOnce(cancel2)

    const { result } = renderHook(() => useSSE())
    act(() => { result.current.search('laksa') })
    act(() => { result.current.search('chicken rice') })
    expect(cancel1).toHaveBeenCalled()
  })

  it('defaults agent to orchestrator when event has no agent', () => {
    mockCreateSearchStream.mockImplementation(
      (_q, _lat, _lng, onEvent) => {
        onEvent({
          type: 'agent_update',
          message: 'Starting...',
        })
        return vi.fn()
      }
    )

    const { result } = renderHook(() => useSSE())
    act(() => { result.current.search('laksa') })
    expect(result.current.traces[0].agent).toBe('orchestrator')
  })
})
