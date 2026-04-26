import { motion, AnimatePresence } from 'framer-motion';
import { useSSE } from './hooks/useSSE';
import { SearchBar } from './components/SearchBar';
import { AgentPanel } from './components/AgentPanel';
import { ResultsList } from './components/ResultsList';
import { ThemeToggle } from './components/ThemeToggle';
import { HawkerMap } from './components/HawkerMap';

function App() {
  const { state, traces, results, error, search, reset } = useSSE();
  const isActive = state !== 'idle';
  const showMap = state === 'complete' && results.length > 0;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="max-w-7xl mx-auto px-4 py-8">

        {/* Header */}
        <header className="flex items-center justify-between mb-8">
          <div
            className="flex items-center gap-2 cursor-pointer group"
            onClick={reset}
          >
            <span className="text-accent text-xl leading-none">●</span>
            <h1 className="text-xl font-semibold text-foreground tracking-tight group-hover:text-foreground/80 transition-colors">
              Hawker Hunt
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <p className="text-subtle text-sm hidden sm:block">Find the best stall. See why.</p>
            <ThemeToggle />
          </div>
        </header>

        {/* Search bar — full width always */}
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

        {/* Content area */}
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

              {/* Results list */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ type: 'spring', stiffness: 300, damping: 30, delay: 0.1 }}
                className="flex-1 min-w-0"
              >
                <ResultsList recommendations={results} state={state} />
              </motion.div>

              {/* Map — right column, sticky, always shown when results ready */}
              {showMap && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.97 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ type: 'spring', stiffness: 300, damping: 30, delay: 0.2 }}
                  className="hidden lg:block lg:w-80 xl:w-96 lg:shrink-0 lg:sticky lg:top-8"
                  style={{ height: 'calc(100vh - 6rem)' }}
                >
                  <HawkerMap recommendations={results} />
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Mobile map — shown below results */}
        {showMap && (
          <div className="lg:hidden mt-4" style={{ height: '320px' }}>
            <HawkerMap recommendations={results} />
          </div>
        )}

      </div>
    </div>
  );
}

export default App;
