import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Map, { NavigationControl } from 'react-map-gl/mapbox';
import 'mapbox-gl/dist/mapbox-gl.css';
import { RankedRecommendation } from '../types';
import { MapMarker } from './MapMarker';
import { MapDetailPanel } from './MapDetailPanel';
import { useTheme } from '../context/ThemeContext';

const TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string | undefined;

interface HawkerMapProps {
  recommendations: RankedRecommendation[];
  /** When true, renders the map canvas directly (no mobile button wrapper). Use inside a sized container. */
  desktopOnly?: boolean;
}

function withCoords(recs: RankedRecommendation[]) {
  return recs.filter(r => r.lat != null && r.lng != null);
}

function getBounds(recs: RankedRecommendation[]): [[number, number], [number, number]] | null {
  const points = withCoords(recs);
  if (points.length === 0) return null;
  const lngs = points.map(r => r.lng!);
  const lats = points.map(r => r.lat!);
  return [
    [Math.min(...lngs), Math.min(...lats)],
    [Math.max(...lngs), Math.max(...lats)],
  ];
}

function MapCanvas({
  recommendations,
  mapStyle,
}: {
  recommendations: RankedRecommendation[];
  mapStyle: string;
}) {
  const [selectedRank, setSelectedRank] = useState<number | null>(null);
  const bounds = getBounds(recommendations);
  const mapped = withCoords(recommendations);

  const selectedRec = selectedRank != null
    ? recommendations.find(r => r.rank === selectedRank) ?? null
    : null;

  const handleMarkerClick = useCallback((rank: number) => {
    setSelectedRank(prev => (prev === rank ? null : rank));
  }, []);

  return (
    <div className="relative w-full h-full">
      <Map
        mapboxAccessToken={TOKEN}
        mapStyle={mapStyle}
        initialViewState={
          bounds
            ? { bounds, fitBoundsOptions: { padding: 60, maxZoom: 15 } }
            : { longitude: 103.8198, latitude: 1.3521, zoom: 12 }
        }
        style={{ width: '100%', height: '100%' }}
      >
        <NavigationControl position="top-right" />
        {mapped.map(rec => (
          <MapMarker
            key={rec.rank}
            recommendation={rec}
            isSelected={selectedRank === rec.rank}
            onClick={() => handleMarkerClick(rec.rank)}
          />
        ))}
      </Map>

      <AnimatePresence>
        {selectedRec && (
          <MapDetailPanel
            recommendation={selectedRec}
            onClose={() => setSelectedRank(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export function HawkerMap({ recommendations, desktopOnly = false }: HawkerMapProps) {
  const { theme } = useTheme();
  const [showMobileMap, setShowMobileMap] = useState(false);

  if (!TOKEN) return null;
  if (withCoords(recommendations).length === 0) return null;

  const mapStyle = theme === 'dark'
    ? 'mapbox://styles/mapbox/dark-v11'
    : 'mapbox://styles/mapbox/light-v11';

  // Desktop-only mode: just render the canvas (parent provides sized container)
  if (desktopOnly) {
    return <MapCanvas recommendations={recommendations} mapStyle={mapStyle} />;
  }

  // Mobile mode: show a "Show map" button that opens a bottom sheet
  return (
    <div className="lg:hidden">
      <button
        onClick={() => setShowMobileMap(true)}
        className="w-full py-2 text-sm text-muted border border-border rounded-xl hover:border-border-strong hover:text-foreground transition-colors"
      >
        Show map ↑
      </button>

      <AnimatePresence>
        {showMobileMap && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/40 z-40"
              onClick={() => setShowMobileMap(false)}
            />
            <motion.div
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="fixed bottom-0 left-0 right-0 h-[60vh] z-50 rounded-t-2xl overflow-hidden border-t border-border"
            >
              <MapCanvas recommendations={recommendations} mapStyle={mapStyle} />
              <button
                onClick={() => setShowMobileMap(false)}
                className="absolute top-3 right-3 w-8 h-8 flex items-center justify-center bg-background/80 backdrop-blur-sm rounded-full border border-border text-muted hover:text-foreground z-10"
              >
                ✕
              </button>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
