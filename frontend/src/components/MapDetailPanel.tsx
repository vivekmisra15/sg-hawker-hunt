import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { RankedRecommendation } from '../types';
import { StatusBadge } from './StatusBadge';

interface MapDetailPanelProps {
  recommendation: RankedRecommendation;
  onClose: () => void;
}

export function MapDetailPanel({ recommendation: r, onClose }: MapDetailPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  // Close on outside click or Escape
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    function handleClick(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        onClose();
      }
    }
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleClick);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleClick);
    };
  }, [onClose]);

  return (
    <motion.div
      ref={panelRef}
      initial={{ opacity: 0, scale: 0.92, y: 8 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.92, y: 8 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      style={{
        transformOrigin: 'bottom center',
        boxShadow: '0 20px 60px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.15)',
      }}
      className="absolute bottom-16 left-1/2 -translate-x-1/2 w-72 backdrop-blur-xl bg-white/10 dark:bg-white/10 border border-white/20 rounded-2xl p-4 z-10"
    >
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-3 right-3 w-5 h-5 flex items-center justify-center text-white/50 hover:text-white/80 transition-colors"
      >
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <h3 className="text-sm font-semibold text-foreground pr-6">{r.stall_name}</h3>
      <p className="text-xs text-muted mt-0.5">{r.centre_name}</p>

      <div className="flex flex-wrap gap-1 mt-2">
        <StatusBadge type="grade" value={r.hygiene_grade} />
        {r.is_michelin && <StatusBadge type="michelin" />}
        <StatusBadge type={r.is_open ? 'open' : 'closed'} />
      </div>

      {r.distance_km < 99 && (
        <p className="text-xs text-muted mt-2 tabular">
          {r.distance_km.toFixed(1)} km away
        </p>
      )}

      <p className="text-xs text-muted mt-2 leading-relaxed line-clamp-2 italic">
        {r.reasoning}
      </p>
    </motion.div>
  );
}
