import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useGeolocation } from '../useGeolocation'

describe('useGeolocation', () => {
  let mockGetCurrentPosition: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockGetCurrentPosition = vi.fn()
    Object.defineProperty(navigator, 'geolocation', {
      value: { getCurrentPosition: mockGetCurrentPosition },
      writable: true,
      configurable: true,
    })
  })

  it('starts with null coordinates and no error', () => {
    const { result } = renderHook(() => useGeolocation())
    expect(result.current.lat).toBeNull()
    expect(result.current.lng).toBeNull()
    expect(result.current.error).toBeNull()
    expect(result.current.loading).toBe(false)
  })

  it('sets loading to true when request is called', () => {
    const { result } = renderHook(() => useGeolocation())
    act(() => { result.current.request() })
    expect(result.current.loading).toBe(true)
  })

  it('sets coordinates on success', () => {
    mockGetCurrentPosition.mockImplementation((success: PositionCallback) => {
      success({
        coords: { latitude: 1.3521, longitude: 103.8198 },
      } as GeolocationPosition)
    })
    const { result } = renderHook(() => useGeolocation())
    act(() => { result.current.request() })
    expect(result.current.lat).toBe(1.3521)
    expect(result.current.lng).toBe(103.8198)
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('sets error on failure', () => {
    mockGetCurrentPosition.mockImplementation(
      (_success: PositionCallback, error: PositionErrorCallback) => {
        error({
          code: 1,
          message: 'User denied',
          PERMISSION_DENIED: 1,
          POSITION_UNAVAILABLE: 2,
          TIMEOUT: 3,
        })
      }
    )
    const { result } = renderHook(() => useGeolocation())
    act(() => { result.current.request() })
    expect(result.current.error).toBe('User denied')
    expect(result.current.lat).toBeNull()
    expect(result.current.loading).toBe(false)
  })

  it('sets error when geolocation is not supported', () => {
    Object.defineProperty(navigator, 'geolocation', {
      value: undefined,
      writable: true,
      configurable: true,
    })
    const { result } = renderHook(() => useGeolocation())
    act(() => { result.current.request() })
    expect(result.current.error).toBe('Geolocation not supported')
  })

  it('clears all state when clear is called', () => {
    mockGetCurrentPosition.mockImplementation((success: PositionCallback) => {
      success({
        coords: { latitude: 1.35, longitude: 103.82 },
      } as GeolocationPosition)
    })
    const { result } = renderHook(() => useGeolocation())
    act(() => { result.current.request() })
    expect(result.current.lat).toBe(1.35)

    act(() => { result.current.clear() })
    expect(result.current.lat).toBeNull()
    expect(result.current.lng).toBeNull()
    expect(result.current.error).toBeNull()
    expect(result.current.loading).toBe(false)
  })
})
