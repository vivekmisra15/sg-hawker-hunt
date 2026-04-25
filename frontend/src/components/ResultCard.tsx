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
  const empty = 5 - full - (hasHalf ? 1 : 0);
  return (
    <span className="flex items-center gap-0.5 text-accent">
      {Array.from({ length: full }).map((_, i) => (
        <svg key={`f${i}`} className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
        </svg>
      ))}
      {hasHalf && (
        <svg className="w-3 h-3" viewBox="0 0 24 24">
          <defs>
            <clipPath id="half">
              <rect x="0" y="0" width="12" height="24" />
            </clipPath>
          </defs>
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="rgb(var(--foreground-subtle))" />
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="currentColor" clipPath="url(#half)" className="text-accent" />
        </svg>
      )}
      {Array.from({ length: empty }).map((_, i) => (
        <svg key={`e${i}`} className="w-3 h-3 text-subtle" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
        </svg>
      ))}
    </span>
  );
}

export function ResultCard({ recommendation: r, index }: ResultCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30, delay: index * 0.07 }}
      whileHover={{ y: -2, scale: 1.01, transition: { type: 'spring', stiffness: 400, damping: 25 } }}
      className="relative bg-card rounded-xl border border-border hover:border-border-strong transition-colors p-5"
    >
      {/* Rank — barely visible watermark */}
      <span className="absolute top-4 right-5 text-5xl font-bold text-foreground/[0.06] leading-none select-none tabular">
        {r.rank}
      </span>

      {/* Name + centre */}
      <div className="pr-12">
        <h3 className="text-base font-semibold text-foreground">{r.stall_name}</h3>
        <p className="text-sm text-muted mt-0.5">{r.centre_name}</p>
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
          <span className="flex items-center gap-1 text-sm text-muted tabular">
            <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {r.distance_km.toFixed(1)} km
          </span>
        )}
        {r.google_rating != null && (
          <span className="flex items-center gap-1.5 text-sm text-muted">
            <StarRating rating={r.google_rating} />
            <span className="tabular">{r.google_rating.toFixed(1)}</span>
          </span>
        )}
      </div>

      {/* Reasoning */}
      <p className="text-sm text-muted italic border-l-2 border-accent/50 pl-3 mt-4 leading-relaxed">
        {r.reasoning}
      </p>
    </motion.div>
  );
}
