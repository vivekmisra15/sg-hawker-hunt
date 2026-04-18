import { useState, useCallback } from 'react';

export interface GeolocationState {
  lat: number | null;
  lng: number | null;
  error: string | null;
  loading: boolean;
}

export function useGeolocation() {
  const [state, setState] = useState<GeolocationState>({
    lat: null,
    lng: null,
    error: null,
    loading: false,
  });

  const request = useCallback(() => {
    if (!navigator.geolocation) {
      setState(s => ({ ...s, error: 'Geolocation not supported' }));
      return;
    }
    setState(s => ({ ...s, loading: true, error: null }));
    navigator.geolocation.getCurrentPosition(
      (pos) => setState({
        lat: pos.coords.latitude,
        lng: pos.coords.longitude,
        error: null,
        loading: false,
      }),
      (err) => setState({
        lat: null,
        lng: null,
        error: err.message,
        loading: false,
      }),
      { timeout: 8000, maximumAge: 60000 },
    );
  }, []);

  const clear = useCallback(() => {
    setState({ lat: null, lng: null, error: null, loading: false });
  }, []);

  return { ...state, request, clear };
}
