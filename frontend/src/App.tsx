import { motion, AnimatePresence } from 'framer-motion';
import { useSSE } from './hooks/useSSE';
import { SearchBar } from './components/SearchBar';
import { AgentPanel } from './components/AgentPanel';
import { ResultsList } from './components/ResultsList';
import { ThemeToggle } from './components/ThemeToggle';
import { HawkerMap } from './components/HawkerMap';

function App() {
  const { state, traces, results, search, reset } = useSSE();
  const isActive = state !== 'idle';
  const showMap = state === 'complete' && results.length > 0;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="max-w-6xl mx-auto px-4 py-8">

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

        {/* Content — single column at idle, two-column when active */}
        <AnimatePresence>
          {isActive && (
            <motion.div
              layout
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: 'spring', stiffness: 280, damping: 32, delay: 0.05 }}
              className="mt-6 flex flex-col lg:flex-row gap-6 items-start"
            >
              {/* Agent panel — sidebar on desktop */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ type: 'spring', stiffness: 300, damping: 30, delay: 0.05 }}
                className="w-full lg:w-72 lg:shrink-0 lg:sticky lg:top-8"
              >
                <AgentPanel traces={traces} state={state} />
              </motion.div>

              {/* Results + map */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ type: 'spring', stiffness: 300, damping: 30, delay: 0.1 }}
                className="flex-1 min-w-0 flex flex-col lg:flex-row gap-6 items-start"
              >
                {/* Results list */}
                <div className="flex-1 min-w-0">
                  <ResultsList recommendations={results} state={state} />

                  {/* Mobile map toggle (below results) */}
                  {showMap && (
                    <div className="mt-4 lg:hidden">
                      <HawkerMap recommendations={results} />
                    </div>
                  )}
                </div>

                {/* Desktop map — right column, sticky */}
                {showMap && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.97 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ type: 'spring', stiffness: 300, damping: 30, delay: 0.15 }}
                    className="hidden lg:block lg:w-80 xl:w-96 lg:shrink-0"
                  >
                    <div className="sticky top-8 h-[calc(100vh-6rem)] rounded-xl overflow-hidden border border-border">
                      <HawkerMap recommendations={results} desktopOnly />
                    </div>
                  </motion.div>
                )}
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </div>
  );
}

export default App;
