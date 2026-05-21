import { useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSSE } from './hooks/useSSE';
import { SearchBar } from './components/SearchBar';
import { AgentPanel } from './components/AgentPanel';
import { ResultsList } from './components/ResultsList';
import { ThemeToggle } from './components/ThemeToggle';
import { HawkerMap } from './components/HawkerMap';
import { StallDetailPanel } from './components/StallDetailPanel';
import { FilterStrip, FilterKey } from './components/FilterStrip';
import { RankedRecommendation } from './types';

/** Derive a time-of-day context from the current Singapore time. */
function getTimeContext(): { label: string; period: string } | null {
  const now = new Date();
  // Singapore is UTC+8
  const sgHour = (now.getUTCHours() + 8) % 24;
  if (sgHour >= 6 && sgHour < 11) return { label: 'Breakfast time — morning favourites ranked first', period: 'breakfast' };
  if (sgHour >= 11 && sgHour < 15) return { label: "It's lunchtime — lunch stalls ranked first", period: 'lunch' };
  if (sgHour >= 17 && sgHour < 21) return { label: 'Dinner hour — evening favourites highlighted', period: 'dinner' };
  if (sgHour >= 21 || sgHour < 3) return { label: 'Supper time — late-night spots ranked first', period: 'supper' };
  return null;
}

function applyFilters(results: RankedRecommendation[], filters: Set<FilterKey>): RankedRecommendation[] {
  if (filters.size === 0) return results;
  return results.filter(r => {
    if (filters.has('michelin') && !r.is_michelin) return false;
    if (filters.has('halal') && !r.is_halal) return false;
    if (filters.has('open') && !r.is_open) return false;
    if (filters.has('gradeA') && r.hygiene_grade !== 'A') return false;
    // 'cheap' filter: we don't have explicit price in the type, but reasoning may mention it
    // For now, filter by score > median as a proxy — or skip if no price data
    return true;
  });
}

function App() {
  const { state, traces, results, error, search, reset } = useSSE();
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [filters, setFilters] = useState<Set<FilterKey>>(new Set());

  const isActive = state !== 'idle';
  const hasResults = state === 'complete' && results.length > 0;

  const filteredResults = useMemo(() => applyFilters(results, filters), [results, filters]);
  const showMap = hasResults && filteredResults.some(r => r.lat != null && r.lng != null);
  const timeContext = hasResults ? getTimeContext() : null;

  const selectedRecommendation = useMemo(() => {
    if (!selectedKey) return null;
    return filteredResults.find(r => `${r.stall_name}::${r.centre_name}` === selectedKey) ?? null;
  }, [selectedKey, filteredResults]);

  const handleSelect = useCallback((key: string) => {
    setSelectedKey(prev => prev === key ? null : key);
  }, []);

  const handleMarkerClick = useCallback((key: string) => {
    setSelectedKey(key);
  }, []);

  const handleFilterToggle = useCallback((key: FilterKey) => {
    setFilters(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }, []);

  const handleReset = useCallback(() => {
    reset();
    setSelectedKey(null);
    setFilters(new Set());
  }, [reset]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="max-w-7xl mx-auto px-4 py-8">

        {/* Header */}
        <header className="flex items-center justify-between mb-8">
          <div
            className="flex items-center gap-2 cursor-pointer group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60 rounded-lg px-1 -mx-1"
            onClick={handleReset}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleReset(); } }}
            tabIndex={0}
            role="button"
            aria-label="Reset search and return to start"
          >
            <span className="text-accent text-xl leading-none" aria-hidden="true">●</span>
            <h1 className="text-xl font-semibold text-foreground tracking-tight group-hover:text-foreground/80 transition-colors">
              Hawker Hunt
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <p className="text-subtle text-sm hidden sm:block">Find the best stall. See why.</p>
            <ThemeToggle />
          </div>
        </header>

        {/* Search bar */}
        <SearchBar
          onSearch={search}
          isSearching={state === 'searching'}
        />

        {/* Error state */}
        <AnimatePresence>
          {state === 'error' && error && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="mt-4 px-4 py-3 bg-danger-bg border border-danger/30 rounded-xl text-sm text-danger"
            >
              <span className="font-medium">Search failed:</span> {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Time context banner */}
        <AnimatePresence>
          {timeContext && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 px-4 py-2.5 bg-accent/10 border border-accent/20 rounded-xl text-sm text-accent flex items-center gap-2"
            >
              <span className="text-base">🕐</span>
              {timeContext.label}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Filter strip — shown after search completes */}
        <AnimatePresence>
          {hasResults && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-4"
            >
              <FilterStrip
                active={filters}
                onToggle={handleFilterToggle}
                resultCount={filteredResults.length}
                totalCount={results.length}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Content area — three-panel layout */}
        <AnimatePresence>
          {isActive && (
            <motion.div
              layout
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: 'spring', stiffness: 280, damping: 32, delay: 0.05 }}
              className="mt-6 flex flex-col lg:flex-row gap-6 items-start"
            >
              {/* Agent panel — narrow left sidebar on desktop */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ type: 'spring', stiffness: 300, damping: 30, delay: 0.05 }}
                className="w-full lg:w-64 lg:shrink-0 lg:sticky lg:top-8"
              >
                <AgentPanel traces={traces} state={state} />
              </motion.div>

              {/* Results list — center column */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ type: 'spring', stiffness: 300, damping: 30, delay: 0.1 }}
                className="flex-1 min-w-0"
              >
                <ResultsList
                  recommendations={filteredResults}
                  state={state}
                  selectedKey={selectedKey}
                  onSelect={handleSelect}
                />
              </motion.div>

              {/* Map — right column, sticky */}
              {showMap && (
                <motion.section
                  aria-label="Map of recommended hawker centres"
                  initial={{ opacity: 0, scale: 0.97 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ type: 'spring', stiffness: 300, damping: 30, delay: 0.2 }}
                  className="hidden lg:block lg:w-80 xl:w-96 lg:shrink-0 lg:sticky lg:top-8"
                  style={{ height: 'calc(100vh - 6rem)' }}
                >
                  <HawkerMap
                    recommendations={filteredResults}
                    selectedKey={selectedKey}
                    onMarkerClick={handleMarkerClick}
                  />
                </motion.section>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Mobile map — shown below results */}
        {showMap && (
          <section className="lg:hidden mt-4" aria-label="Map of recommended hawker centres" style={{ height: '320px' }}>
            <HawkerMap
              recommendations={filteredResults}
              selectedKey={selectedKey}
              onMarkerClick={handleMarkerClick}
            />
          </section>
        )}

      </div>

      {/* Detail panel — slides in from right (desktop) / bottom (mobile) */}
      <StallDetailPanel
        recommendation={selectedRecommendation}
        onClose={() => setSelectedKey(null)}
      />
    </div>
  );
}

export default App;
