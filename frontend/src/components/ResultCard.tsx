import { motion } from 'framer-motion';
import { RankedRecommendation } from '../types';
import { StatusBadge } from './StatusBadge';

interface ResultCardProps {
  recommendation: RankedRecommendation;
  index: number;
}

function StarRating({ rating }: { rating: number }) {
  const full = Math.floor(rating);
  const hasHalf = rating - full >= 0.5;
  return (
    <span className="text-amber-400 text-sm">
      {'★'.repeat(full)}
      {hasHalf ? '½' : ''}
      {'☆'.repeat(5 - full - (hasHalf ? 1 : 0))}
    </span>
  );
}

export function ResultCard({ recommendation: r, index }: ResultCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.4, ease: 'easeOut' }}
      className="relative bg-[#1a1a1a] rounded-xl border border-white/10 p-5 hover:border-white/20 transition-all"
    >
      {/* Rank */}
      <span className="absolute top-4 right-5 text-5xl font-bold text-white/10 leading-none select-none">
        {r.rank}
      </span>

      {/* Name + centre */}
      <div className="pr-12">
        <h3 className="text-lg font-semibold text-white">{r.stall_name}</h3>
        <p className="text-sm text-white/50 mt-0.5">{r.centre_name}</p>
      </div>

      {/* Badges */}
      <div className="flex flex-wrap gap-1.5 mt-3">
        <StatusBadge type="grade" value={r.hygiene_grade} />
        {r.is_michelin && <StatusBadge type="michelin" />}
        {r.is_halal && <StatusBadge type="halal" />}
        <StatusBadge type={r.is_open ? 'open' : 'closed'} />
      </div>

      {/* Distance + rating row */}
      <div className="flex items-center gap-4 mt-3">
        {r.distance_km < 99 && (
          <span className="text-sm text-white/40">
            📍 {r.distance_km.toFixed(1)} km
          </span>
        )}
        {r.google_rating !== undefined && r.google_rating !== null && (
          <span className="flex items-center gap-1.5 text-sm text-white/50">
            <StarRating rating={r.google_rating} />
            <span>{r.google_rating.toFixed(1)}</span>
          </span>
        )}
      </div>

      {/* Reasoning */}
      <p className="text-sm text-white/60 italic border-l-2 border-amber-500/40 pl-3 mt-4 leading-relaxed">
        {r.reasoning}
      </p>
    </motion.div>
  );
}
