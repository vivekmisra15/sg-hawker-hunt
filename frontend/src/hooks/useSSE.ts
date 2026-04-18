import { useState, useCallback, useRef } from 'react';
import { AgentEvent, RankedRecommendation } from '../types';
import { createSearchStream } from '../lib/api';

export type SearchState = 'idle' | 'searching' | 'complete' | 'error';

export interface AgentTrace {
  agent: string;
  message: string;
  timestamp: number;
}

export function useSSE() {
  const [state, setState] = useState<SearchState>('idle');
  const [traces, setTraces] = useState<AgentTrace[]>([]);
  const [results, setResults] = useState<RankedRecommendation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const cancelRef = useRef<(() => void) | null>(null);

  const search = useCallback((
    query: string,
    lat?: number,
    lng?: number,
  ) => {
    // Cancel any in-flight request
    cancelRef.current?.();

    // Reset state
    setState('searching');
    setTraces([]);
    setResults([]);
    setError(null);

    cancelRef.current = createSearchStream(
      query, lat, lng,
      (event: AgentEvent) => {
        if (event.type === 'agent_update') {
          setTraces(prev => [...prev, {
            agent: event.agent ?? 'orchestrator',
            message: event.message ?? '',
            timestamp: Date.now(),
          }]);
        } else if (event.type === 'result') {
          const data = event.data as { recommendations: RankedRecommendation[] };
          setResults(data?.recommendations ?? []);
          setState('complete');
        } else if (event.type === 'error') {
          setError(event.message ?? 'Unknown error');
          setState('error');
        }
      },
      (err) => { setError(err); setState('error'); },
      () => { setState(s => s === 'searching' ? 'complete' : s); },
    );
  }, []);

  const reset = useCallback(() => {
    cancelRef.current?.();
    setState('idle');
    setTraces([]);
    setResults([]);
    setError(null);
  }, []);

  return { state, traces, results, error, search, reset };
}
