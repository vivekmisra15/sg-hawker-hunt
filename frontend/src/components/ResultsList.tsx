import { useState, useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { RankedRecommendation } from '../types';
import { SearchState } from '../hooks/useSSE';
import { ResultCard } from './ResultCard';

interface ResultsListProps {
  recommendations: RankedRecommendation[];
  state: SearchState;
}

export function ResultsList({ recommendations, state }: ResultsListProps) {
  const [visibleCount, setVisibleCount] = useState(5);
  const sentinelRef = useRef<HTMLDivElement>(null);

  // Reset when new results come in
  useEffect(() => {
    setVisibleCount(5);
  }, [recommendations]);

  // IntersectionObserver: reveal 5 more when sentinel enters viewport
  useEffect(() => {
    if (visibleCount >= recommendations.length) return;
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setVisibleCount(c => Math.min(c + 5, recommendations.length));
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [visibleCount, recommendations.length]);

  if (state !== 'complete') return null;

  if (recommendations.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center py-12 text-muted"
      >
        <div className="text-4xl mb-3">🍽️</div>
        <p className="text-sm">No stalls found matching your search. Try a different query.</p>
      </motion.div>
    );
  }

  const visible = recommendations.slice(0, visibleCount);
  const hasMore = visibleCount < recommendations.length;

  return (
    <div className="space-y-3">
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
          {visibleCount} of {recommendations.length}
        </p>
      </div>

      <AnimatePresence>
        {visible.map((rec, i) => (
          <ResultCard key={rec.stall_name + rec.centre_name} recommendation={rec} index={i} />
        ))}
      </AnimatePresence>

      {/* Sentinel div — triggers infinite scroll */}
      {hasMore && (
        <div ref={sentinelRef} className="py-4 text-center">
          <span className="text-xs text-subtle">↓ scroll for more</span>
        </div>
      )}
    </div>
  );
}
