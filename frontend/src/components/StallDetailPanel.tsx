import { useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RankedRecommendation } from '../types';
import { StatusBadge } from './StatusBadge';

interface StallDetailPanelProps {
  recommendation: RankedRecommendation | null;
  onClose: () => void;
}

const FOCUSABLE_SELECTOR = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

function mapsUrl(stallName: string, centreName: string) {
  return `https://www.google.com/maps/search/?api=1&query=${
    encodeURIComponent(`${stallName} ${centreName} Singapore`)
  }`;
}

export function StallDetailPanel({ recommendation: r, onClose }: StallDetailPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const previouslyFocusedRef = useRef<HTMLElement | null>(null);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
      return;
    }

    // Focus trap: cycle Tab within the panel
    if (e.key === 'Tab' && panelRef.current) {
      const focusable = Array.from(
        panelRef.current.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
      );
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }
  }, [onClose]);

  // Manage focus: save previous, move into panel, restore on close
  useEffect(() => {
    if (r) {
      previouslyFocusedRef.current = document.activeElement as HTMLElement;
      // Focus the close button after the panel animates in
      const timer = setTimeout(() => {
        if (panelRef.current) {
          const closeBtn = panelRef.current.querySelector<HTMLElement>('button[aria-label="Close detail panel"]');
          closeBtn?.focus();
        }
      }, 100);
      return () => clearTimeout(timer);
    } else if (previouslyFocusedRef.current) {
      previouslyFocusedRef.current.focus();
      previouslyFocusedRef.current = null;
    }
  }, [r]);

  // Keyboard listener
  useEffect(() => {
    if (!r) return;
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [r, handleKeyDown]);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        onClose();
      }
    }
    if (r) {
      // Delay to avoid catching the click that opened the panel
      const timer = setTimeout(() => document.addEventListener('mousedown', handleClick), 50);
      return () => {
        clearTimeout(timer);
        document.removeEventListener('mousedown', handleClick);
      };
    }
  }, [r, onClose]);

  return (
    <AnimatePresence>
      {r && (
        <>
          {/* Backdrop — mobile only */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/40 z-40 lg:hidden"
            onClick={onClose}
          />

          {/* Panel — slide from right on desktop, sheet from bottom on mobile */}
          <motion.div
            ref={panelRef}
            initial={{ x: '100%', opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: '100%', opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-md bg-card border-l border-border shadow-2xl overflow-y-auto
                       max-lg:top-auto max-lg:bottom-0 max-lg:left-0 max-lg:right-0 max-lg:max-w-none max-lg:h-[75vh] max-lg:rounded-t-2xl max-lg:border-l-0 max-lg:border-t"
            role="dialog"
            aria-label={`Details for ${r.stall_name}`}
            aria-modal="true"
          >
            {/* Drag handle — mobile */}
            <div className="lg:hidden flex justify-center pt-3 pb-1">
              <div className="w-10 h-1 rounded-full bg-border-strong" />
            </div>

            {/* Close button */}
            <button
              onClick={onClose}
              aria-label="Close detail panel"
              className="absolute top-4 right-4 p-2 rounded-lg text-subtle hover:text-foreground hover:bg-background-raised transition-colors z-10"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            <div className="p-6 pt-4 lg:pt-6 space-y-5">
              {/* Rank badge */}
              <div className="flex items-start gap-3">
                <span className="flex-shrink-0 w-10 h-10 rounded-full bg-accent text-accent-foreground flex items-center justify-center font-bold text-lg tabular">
                  {r.rank}
                </span>
                <div className="min-w-0">
                  <h2 className="text-lg font-semibold text-foreground leading-tight">{r.stall_name}</h2>
                  <p className="text-sm text-muted mt-0.5">{r.centre_name}</p>
                </div>
              </div>

              {/* Badges */}
              <div className="flex flex-wrap gap-1.5">
                <StatusBadge type="grade" value={r.hygiene_grade} />
                {r.is_michelin && <StatusBadge type="michelin" />}
                {r.is_halal && <StatusBadge type="halal" />}
                <StatusBadge type={r.is_open ? 'open' : 'closed'} />
                {(r.crowd_level === 'busy' || r.crowd_level === 'quiet') && r.is_open && (
                  <StatusBadge type="crowd" value={r.crowd_level} />
                )}
                {r.price_category && <StatusBadge type="price" value={r.price_category} />}
              </div>

              {/* Stats row */}
              <div className="grid grid-cols-2 gap-3">
                {r.distance_km < 99 && (
                  <div className="bg-background-subtle rounded-lg p-3">
                    <p className="text-xs text-subtle uppercase tracking-wider mb-1">Distance</p>
                    <p className="text-base font-semibold text-foreground tabular">{r.distance_km.toFixed(1)} km</p>
                  </div>
                )}
                {r.google_rating != null && (
                  <div className="bg-background-subtle rounded-lg p-3">
                    <p className="text-xs text-subtle uppercase tracking-wider mb-1">Rating</p>
                    <p className="text-base font-semibold text-foreground tabular">
                      <span className="text-accent">★</span> {r.google_rating.toFixed(1)}
                      {r.review_count != null && (
                        <span className="text-xs text-subtle font-normal ml-1">({r.review_count.toLocaleString()})</span>
                      )}
                    </p>
                  </div>
                )}
                {r.score != null && (
                  <div className="bg-background-subtle rounded-lg p-3">
                    <p className="text-xs text-subtle uppercase tracking-wider mb-1">Score</p>
                    <p className="text-base font-semibold text-foreground tabular">{r.score.toFixed(1)}</p>
                  </div>
                )}
              </div>

              {/* Standout quote */}
              {r.standout_quote && (
                <blockquote className="border-l-2 border-accent/50 pl-3 py-1">
                  <p className="text-sm text-muted italic leading-relaxed">"{r.standout_quote}"</p>
                  <p className="text-xs text-subtle mt-1">— Google Reviews</p>
                </blockquote>
              )}

              {/* Reasoning */}
              <div>
                <p className="text-xs text-subtle uppercase tracking-wider mb-2">Why this stall</p>
                <p className="text-sm text-muted leading-relaxed">{r.reasoning}</p>
              </div>

              {/* Google Maps CTA */}
              <a
                href={mapsUrl(r.stall_name, r.centre_name)}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full py-3 bg-accent hover:bg-accent/90 text-accent-foreground font-medium rounded-xl transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Open in Google Maps
              </a>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
