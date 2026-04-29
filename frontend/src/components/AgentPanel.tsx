import { useEffect, useRef, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AgentTrace, SearchState } from '../hooks/useSSE';

const AGENT_LABELS: Record<string, string> = {
  orchestrator: 'Orchestrator',
  location: 'Location',
  hygiene: 'Hygiene',
  recommendation: 'Recommendation',
};

interface AgentBlock {
  agent: string;
  messages: { message: string; timestamp: number; isNew: boolean }[];
}

interface AgentPanelProps {
  traces: AgentTrace[];
  state: SearchState;
}

/** Detect OS prefers-reduced-motion via matchMedia, with SSR-safe default. */
function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  });

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  return reduced;
}

function TypewriterText({ text, isNew }: { text: string; isNew: boolean }) {
  const prefersReducedMotion = usePrefersReducedMotion();

  // When reduced motion is preferred, or the line is not new, render plain text
  if (!isNew || prefersReducedMotion) {
    return <span className="dark:text-green-300/70 text-emerald-800/80">{text}</span>;
  }
  return (
    <span>
      {text.split('').map((char, i) => (
        <motion.span
          key={i}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: i * 0.018, duration: 0 }}
          className="dark:text-green-300/70 text-emerald-800/80"
        >
          {char}
        </motion.span>
      ))}
    </span>
  );
}

export function AgentPanel({ traces, state }: AgentPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const prevTraceLengthRef = useRef(0);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [traces]);

  // Group traces into named blocks, marking only the newest line as new
  const blocks = useMemo<AgentBlock[]>(() => {
    const blockMap = new Map<string, AgentBlock>();
    const agentOrder: string[] = [];

    traces.forEach((trace, idx) => {
      if (!blockMap.has(trace.agent)) {
        blockMap.set(trace.agent, { agent: trace.agent, messages: [] });
        agentOrder.push(trace.agent);
      }
      blockMap.get(trace.agent)!.messages.push({
        message: trace.message,
        timestamp: trace.timestamp,
        isNew: idx === traces.length - 1 && idx >= prevTraceLengthRef.current,
      });
    });

    prevTraceLengthRef.current = traces.length;
    return agentOrder.map(a => blockMap.get(a)!);
  }, [traces]);

  return (
    <div className="bg-background-subtle rounded-xl border border-border overflow-hidden">
      {/* Terminal header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
        <div className="flex gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-border-strong" />
          <span className="w-2.5 h-2.5 rounded-full bg-border-strong" />
          <span className="w-2.5 h-2.5 rounded-full bg-border-strong" />
        </div>
        <span className="text-xs text-subtle font-mono">agent trace</span>
      </div>

      <div
        ref={scrollRef}
        role="log"
        aria-live="polite"
        aria-label="Agent reasoning trace"
        className="h-48 md:h-56 overflow-y-auto scroll-smooth"
      >
        {state === 'idle' && (
          <div className="h-full flex items-center justify-center text-subtle text-xs font-mono">
            Agents ready. Enter a query to begin.
          </div>
        )}

        {blocks.length > 0 && (
          <div className="font-mono text-xs">
            <AnimatePresence initial={false}>
              {blocks.map((block, blockIdx) => (
                <motion.div
                  key={block.agent}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{
                    type: 'spring',
                    stiffness: 400,
                    damping: 30,
                    delay: blockIdx * 0.08,
                  }}
                >
                  {/* Block header */}
                  <div className="flex items-center gap-2 px-4 py-1.5 border-t border-border first:border-t-0">
                    <span className="text-subtle uppercase tracking-widest text-[10px]">
                      {AGENT_LABELS[block.agent] ?? block.agent}
                    </span>
                    <div className="flex-1 h-px bg-border" />
                  </div>

                  {/* Block messages */}
                  <div className="px-4 pb-2 space-y-0.5">
                    {block.messages.map(msg => (
                      <div key={msg.timestamp} className="leading-relaxed">
                        <TypewriterText text={msg.message} isNew={msg.isNew} />
                      </div>
                    ))}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Blinking cursor while searching */}
            {state === 'searching' && (
              <div className="px-4 pb-2">
                <span className="cursor-blink dark:text-green-400 text-emerald-700">▊</span>
              </div>
            )}

            {/* Complete indicator */}
            {state === 'complete' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="px-4 py-2 border-t border-border flex items-center gap-1.5 text-[10px] text-success"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Analysis complete
              </motion.div>
            )}

            {/* Error indicator */}
            {state === 'error' && (
              <div className="px-4 py-2 border-t border-border text-[10px] text-danger">
                ✗ Error — check API keys or try again
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
