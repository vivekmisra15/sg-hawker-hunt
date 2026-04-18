import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AgentTrace, SearchState } from '../hooks/useSSE';

const AGENT_ICONS: Record<string, string> = {
  orchestrator: '🔍',
  location: '📍',
  hygiene: '🧼',
  recommendation: '⭐',
};

interface AgentPanelProps {
  traces: AgentTrace[];
  state: SearchState;
}

export function AgentPanel({ traces, state }: AgentPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [traces]);

  return (
    <div className="bg-[#111111] rounded-xl border border-white/10 p-4">
      <div className="flex items-center gap-2 mb-3">
        <div className="flex gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-white/10" />
          <span className="w-2.5 h-2.5 rounded-full bg-white/10" />
          <span className="w-2.5 h-2.5 rounded-full bg-white/10" />
        </div>
        <span className="text-xs text-white/30 font-mono">agent trace</span>
      </div>

      <div
        ref={scrollRef}
        className="h-48 md:h-64 overflow-y-auto font-mono text-sm space-y-1 scroll-smooth"
      >
        {state === 'idle' && (
          <div className="h-full flex items-center justify-center text-white/30 text-xs">
            Agents ready. Enter a query to begin.
          </div>
        )}

        <AnimatePresence initial={false}>
          {traces.map((trace, i) => (
            <motion.div
              key={trace.timestamp}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: i === traces.length - 1 ? 0 : 0 }}
              className="flex gap-2 text-green-300/80"
            >
              <span className="shrink-0 w-5 text-center">
                {AGENT_ICONS[trace.agent] ?? '▸'}
              </span>
              <span className="text-white/50 shrink-0">{trace.agent}</span>
              <span className="text-green-300/70">{trace.message}</span>
            </motion.div>
          ))}
        </AnimatePresence>

        {state === 'searching' && traces.length > 0 && (
          <div className="flex gap-2 text-green-300/80">
            <span className="shrink-0 w-5 text-center">▸</span>
            <span className="cursor-blink text-green-400">▊</span>
          </div>
        )}

        {state === 'complete' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-2 text-green-400 text-xs mt-1 pt-1 border-t border-white/5"
          >
            <span>✓ Analysis complete</span>
          </motion.div>
        )}

        {state === 'error' && (
          <div className="text-red-400 text-xs mt-1">
            ✗ Error — check API keys or try again
          </div>
        )}
      </div>
    </div>
  );
}
