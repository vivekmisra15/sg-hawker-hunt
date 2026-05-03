import { AgentEvent } from '../types';

const BASE_URL = '/api';

/** Maximum time (ms) to wait for the entire SSE stream before aborting. */
const STREAM_TIMEOUT_MS = 120_000;

export function createSearchStream(
  query: string,
  lat: number | undefined,
  lng: number | undefined,
  onEvent: (event: AgentEvent) => void,
  onError: (error: string) => void,
  onComplete: () => void
): () => void {
  const controller = new AbortController();
  let userCancelled = false;

  // Auto-abort after timeout so the UI never hangs in "searching" state
  const timeoutId = setTimeout(() => controller.abort(), STREAM_TIMEOUT_MS);

  fetch(`${BASE_URL}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, lat, lng }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const parsed = JSON.parse(line.slice(6));
                onEvent(parsed as AgentEvent);
              } catch {
                // skip malformed SSE data lines
              }
            }
          }
        }
      } finally {
        // Always signal completion so the UI leaves "searching" state,
        // even if reader.read() threw (e.g., network disconnect mid-stream)
        onComplete();
      }
    })
    .catch((err) => {
      if (err.name === 'AbortError') {
        // Only show error for timeout-triggered aborts, not user cancellation
        if (!userCancelled) {
          onError('Search timed out. Please try again.');
        }
      } else {
        onError(err.message);
      }
    })
    .finally(() => {
      clearTimeout(timeoutId);
    });

  return () => {
    userCancelled = true;
    clearTimeout(timeoutId);
    controller.abort();
  };
}
