import { AnimatePresence, motion } from 'framer-motion';
import { RankedRecommendation } from '../types';
import { SearchState } from '../hooks/useSSE';
import { ResultCard } from './ResultCard';

interface ResultsListProps {
  recommendations: RankedRecommendation[];
  state: SearchState;
}

export function ResultsList({ recommendations, state }: ResultsListProps) {
  if (state !== 'complete') return null;

  if (recommendations.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center py-12 text-white/30"
      >
        <div className="text-4xl mb-3">🍽️</div>
        <p className="text-sm">No stalls found matching your search. Try a different query.</p>
      </motion.div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-white/40 uppercase tracking-wider font-medium">
        Top picks for you
      </p>
      <AnimatePresence>
        {recommendations.map((rec, i) => (
          <ResultCard key={rec.stall_name + rec.centre_name} recommendation={rec} index={i} />
        ))}
      </AnimatePresence>
    </div>
  );
}
