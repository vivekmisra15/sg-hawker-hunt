import { motion } from 'framer-motion';

export type FilterKey = 'michelin' | 'halal' | 'open' | 'gradeA' | 'cheap';

interface FilterStripProps {
  active: Set<FilterKey>;
  onToggle: (key: FilterKey) => void;
  resultCount: number;
  totalCount: number;
}

const FILTERS: { key: FilterKey; label: string; icon: string }[] = [
  { key: 'michelin', label: 'Michelin', icon: '★' },
  { key: 'halal', label: 'Halal', icon: '☾' },
  { key: 'open', label: 'Open now', icon: '●' },
  { key: 'gradeA', label: 'Grade A', icon: 'A' },
  { key: 'cheap', label: 'Under $5', icon: '$' },
];

export function FilterStrip({ active, onToggle, resultCount, totalCount }: FilterStripProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="flex items-center gap-2 flex-wrap"
    >
      {FILTERS.map(({ key, label, icon }) => {
        const isActive = active.has(key);
        return (
          <button
            key={key}
            type="button"
            onClick={() => onToggle(key)}
            aria-pressed={isActive}
            aria-label={`Filter: ${label}`}
            className={`
              inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium
              transition-all duration-150 cursor-pointer
              ${isActive
                ? 'bg-accent text-accent-foreground shadow-sm shadow-accent/20'
                : 'bg-transparent border border-border text-muted hover:border-border-strong hover:text-foreground'
              }
            `}
          >
            <span className={`text-[10px] ${isActive ? 'opacity-100' : 'opacity-60'}`}>{icon}</span>
            {label}
          </button>
        );
      })}

      {/* Count indicator when filters are active */}
      {active.size > 0 && (
        <motion.span
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-xs text-subtle ml-1 tabular"
        >
          {resultCount} of {totalCount}
        </motion.span>
      )}
    </motion.div>
  );
}
