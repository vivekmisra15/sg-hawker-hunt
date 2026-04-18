import { useSSE } from './hooks/useSSE';
import { SearchBar } from './components/SearchBar';
import { AgentPanel } from './components/AgentPanel';
import { ResultsList } from './components/ResultsList';

function App() {
  const { state, traces, results, search, reset } = useSSE();

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">

        {/* Header */}
        <header className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-amber-400 text-xl leading-none">●</span>
            <h1
              className="text-2xl font-semibold text-white tracking-tight cursor-pointer"
              onClick={reset}
            >
              Hawker Hunt
            </h1>
          </div>
          <p className="text-white/40 text-sm pl-6">Find the best stall. See why.</p>
        </header>

        {/* Search */}
        <SearchBar
          onSearch={search}
          isSearching={state === 'searching'}
        />

        {/* Agent panel — shown during and after search */}
        {state !== 'idle' && (
          <AgentPanel traces={traces} state={state} />
        )}

        {/* Results */}
        <ResultsList recommendations={results} state={state} />

      </div>
    </div>
  );
}

export default App;
