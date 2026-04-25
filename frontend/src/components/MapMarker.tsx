import { motion } from 'framer-motion';
import { Marker } from 'react-map-gl/mapbox';
import { RankedRecommendation } from '../types';

interface MapMarkerProps {
  recommendation: RankedRecommendation;
  isSelected: boolean;
  onClick: () => void;
}

export function MapMarker({ recommendation: r, isSelected, onClick }: MapMarkerProps) {
  if (r.lat == null || r.lng == null) return null;

  return (
    <Marker longitude={r.lng} latitude={r.lat} anchor="bottom" onClick={onClick}>
      <motion.div
        initial={{ y: -16, opacity: 0, scale: 0.6 }}
        animate={{ y: 0, opacity: 1, scale: 1 }}
        transition={{
          type: 'spring',
          stiffness: 500,
          damping: 25,
          delay: r.rank * 0.08,
        }}
        whileHover={{ scale: 1.1, transition: { type: 'spring', stiffness: 400, damping: 20 } }}
        className="cursor-pointer select-none"
      >
        <motion.div
          animate={isSelected ? { scale: [1.0, 1.3, 1.1] } : { scale: 1 }}
          transition={isSelected ? { type: 'spring', stiffness: 400, damping: 15 } : {}}
          className="relative"
        >
          {/* Pulse ring when selected */}
          {isSelected && (
            <motion.div
              initial={{ opacity: 0.6, scale: 1 }}
              animate={{ opacity: 0, scale: 1.8 }}
              transition={{ duration: 0.6, repeat: Infinity, repeatDelay: 0.4 }}
              className="absolute inset-0 rounded-full"
              style={{ backgroundColor: 'rgba(245,158,11,0.4)' }}
            />
          )}

          {/* Marker pin */}
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-black tabular"
            style={{
              backgroundColor: 'rgb(var(--accent))',
              boxShadow: isSelected
                ? '0 0 0 3px rgba(245,158,11,0.5), 0 4px 12px rgba(0,0,0,0.4)'
                : '0 2px 8px rgba(0,0,0,0.3)',
            }}
          >
            {r.rank}
          </div>
        </motion.div>
      </motion.div>
    </Marker>
  );
}
