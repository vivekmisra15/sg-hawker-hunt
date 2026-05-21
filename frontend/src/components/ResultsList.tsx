import { useState, useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { RankedRecommendation } from '../types';
import { SearchState } from '../hooks/useSSE';
import { ResultCard } from './ResultCard';

interface ResultsListProps {
  recommendations: RankedRecommendation[];
  state: SearchState;
  selectedKey?: string | null;
  onSelect?: (key: string) => void;
}

export function ResultsList({ recommendations, state, selectedKey, onSelect }: ResultsListProps) {
  const [visibleCount, setVisibleCount] = useState(5);
  const sentinelRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const totalRef = useRef(recommendations.length);
  totalRef.current = recommendations.length;

  // Reset when new results come in
  useEffect(() => {
    setVisibleCount(5);
  }, [recommendations]);

  // IntersectionObserver: reveal 5 more when sentinel enters viewport
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setVisibleCount(c => Math.min(c + 5, totalRef.current));
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [recommendations]);

  // Scroll to selected card when selectedKey changes (from map click)
  useEffect(() => {
    if (!selectedKey || !containerRef.current) return;
    const card = containerRef.current.querySelector(`[data-key="${CSS.escape(selectedKey)}"]`);
    if (card) {
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [selectedKey]);

  if (state !== 'complete') return null;

  if (recommendations.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center py-12 text-muted"
      >
        <svg className="w-10 h-10 mx-auto mb-3 text-subtle" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <p className="text-sm">No stalls found matching your search. Try a different query.</p>
      </motion.div>
    );
  }

  const visible = recommendations.slice(0, visibleCount);
  const hasMore = visibleCount < recommendations.length;

  return (
    <div ref={containerRef} className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <p className="text-xs text-subtle uppercase tracking-wider font-medium">
            Top picks
          </p>
          <svg className="overflow-visible" width="40" height="4" viewBox="0 0 40 4">
            <motion.path
              d="M0 2 Q20 0 40 2"
              stroke="rgb(var(--accent))"
              strokeWidth="2"
              fill="none"
              strokeLinecap="round"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{ duration: 0.6, ease: 'easeOut', delay: 0.2 }}
            />
          </svg>
        </div>
        <p className="text-xs text-subtle tabular">
          {Math.min(visibleCount, recommendations.length)} of {recommendations.length}
        </p>
      </div>

      <AnimatePresence>
        {visible.map((rec, i) => (
          <ResultCard
            key={rec.stall_name + rec.centre_name}
            recommendation={rec}
            index={i}
            isSelected={`${rec.stall_name}::${rec.centre_name}` === selectedKey}
            onSelect={onSelect}
          />
        ))}
      </AnimatePresence>

      {/* Sentinel div — always mounted so observer can attach */}
      <div ref={sentinelRef} className="py-4 text-center">
        {hasMore && <span className="text-xs text-subtle">↓ scroll for more</span>}
      </div>
    </div>
  );
}
