import { useState, useRef, KeyboardEvent } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useGeolocation } from '../hooks/useGeolocation';

interface SearchBarProps {
  onSearch: (query: string, lat?: number, lng?: number) => void;
  isSearching: boolean;
}

const EXAMPLE_CHIPS = [
  '🍜 Chicken rice near me',
  '🌶️ Laksa, not too crowded',
  '🥗 Vegetarian options',
  '⭐ Michelin stalls only',
];

export function SearchBar({ onSearch, isSearching }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const { lat, lng, loading: geoLoading, request: requestGeo } = useGeolocation();

  const hasLocation = lat !== null && lng !== null;

  function handleSubmit() {
    const q = query.trim();
    if (!q || isSearching) return;
    onSearch(q, lat ?? undefined, lng ?? undefined);
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') handleSubmit();
  }

  function handleChip(chip: string) {
    const text = chip.replace(/^[\p{Emoji}\s]+/u, '').trim();
    setQuery(text);
    inputRef.current?.focus();
  }

  return (
    <div className="w-full space-y-3">
      {/* Input row — glass morphism */}
      <div className="relative flex items-center bg-background-raised/80 backdrop-blur-sm border border-border rounded-xl transition-all duration-200 focus-within:border-accent/60 focus-within:ring-2 focus-within:ring-accent/20">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSearching}
          placeholder="Find hawker food... try 'laksa near Toa Payoh' or 'vegetarian Maxwell'"
          className="flex-1 bg-transparent px-4 py-3 text-base text-foreground placeholder-subtle outline-none disabled:opacity-50"
        />

        {/* Location button */}
        <button
          type="button"
          onClick={requestGeo}
          disabled={isSearching}
          title={hasLocation ? `${lat?.toFixed(4)}, ${lng?.toFixed(4)}` : 'Use my location'}
          className={`p-2 mr-1 rounded-lg transition-colors disabled:opacity-40 ${
            hasLocation
              ? 'text-accent hover:bg-accent/10'
              : 'text-subtle hover:text-muted hover:bg-border'
          }`}
        >
          {geoLoading ? (
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          )}
        </button>

        {/* Submit button with icon morph */}
        <button
          type="button"
          onClick={handleSubmit}
          disabled={isSearching || !query.trim()}
          className="mr-2 px-3 py-1.5 bg-accent hover:bg-accent/90 disabled:bg-border disabled:text-subtle text-accent-foreground text-sm font-medium rounded-lg transition-colors flex items-center gap-1.5"
        >
          <AnimatePresence mode="wait" initial={false}>
            {isSearching ? (
              <motion.span
                key="spinner"
                initial={{ scale: 0.5, rotate: 45, opacity: 0 }}
                animate={{ scale: 1, rotate: 0, opacity: 1 }}
                exit={{ scale: 0.5, opacity: 0 }}
                transition={{ type: 'spring', stiffness: 400, damping: 20 }}
              >
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
              </motion.span>
            ) : (
              <motion.span
                key="arrow"
                initial={{ scale: 0.5, rotate: -45, opacity: 0 }}
                animate={{ scale: 1, rotate: 0, opacity: 1 }}
                exit={{ scale: 0.5, rotate: -45, opacity: 0 }}
                transition={{ type: 'spring', stiffness: 400, damping: 20 }}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </motion.span>
            )}
          </AnimatePresence>
        </button>
      </div>

      {/* Example chips */}
      <div className="flex flex-wrap gap-2">
        {EXAMPLE_CHIPS.map(chip => (
          <button
            key={chip}
            type="button"
            onClick={() => handleChip(chip)}
            className="text-xs bg-border/60 hover:bg-border text-muted hover:text-foreground rounded-full px-3 py-1 transition-colors cursor-pointer"
          >
            {chip}
          </button>
        ))}
      </div>
    </div>
  );
}
