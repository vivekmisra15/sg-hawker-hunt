import { useEffect, useRef, useCallback } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { RankedRecommendation } from '../types';
import { useTheme } from '../context/ThemeContext';

interface HawkerMapProps {
  recommendations: RankedRecommendation[];
  selectedKey?: string | null;
  onMarkerClick?: (key: string) => void;
}

const LIGHT_TILES = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
const DARK_TILES  = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const TILE_ATTR   = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

const GRADE_COLORS: Record<string, string> = {
  A: '#16a34a',
  B: '#d97706',
  C: '#dc2626',
  D: '#dc2626',
};

function withCoords(recs: RankedRecommendation[]) {
  return recs.filter(r => r.lat != null && r.lng != null);
}

function mapsUrl(stallName: string, centreName: string) {
  return `https://www.google.com/maps/search/?api=1&query=${
    encodeURIComponent(`${stallName} ${centreName} Singapore`)
  }`;
}

function makeMarkerIcon(rec: RankedRecommendation, isSelected: boolean): L.DivIcon {
  const grade = rec.hygiene_grade;
  const color = GRADE_COLORS[grade] ?? '#737373';
  const label = grade === 'UNKNOWN' ? '—' : grade;
  const size = isSelected ? 42 : 34;
  const borderWidth = isSelected ? 3 : 2;
  const fontSize = isSelected ? 16 : 13;
  const shadow = isSelected
    ? `box-shadow:0 0 0 4px ${color}40, 0 4px 12px rgba(0,0,0,0.4);`
    : 'box-shadow:0 2px 8px rgba(0,0,0,0.35);';

  return L.divIcon({
    className: '',
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
    popupAnchor: [0, -size - 2],
    html: `
      <div style="
        width:${size}px;height:${size}px;border-radius:50%;
        background:${color};color:#fff;
        display:flex;align-items:center;justify-content:center;
        font-family:Geist,DM Sans,system-ui,sans-serif;
        font-size:${fontSize}px;font-weight:700;font-variant-numeric:tabular-nums;
        ${shadow}
        border:${borderWidth}px solid rgba(255,255,255,0.85);
        transition:all 0.2s ease;
        z-index:${isSelected ? 1000 : 'auto'};
      ">${label}</div>
    `,
  });
}

export function markerKey(rec: RankedRecommendation): string {
  return `${rec.stall_name}::${rec.centre_name}`;
}

export function HawkerMap({ recommendations, selectedKey, onMarkerClick }: HawkerMapProps) {
  const { theme } = useTheme();
  const mapRef = useRef<L.Map | null>(null);
  const tileRef = useRef<L.TileLayer | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const markersRef = useRef<Map<string, L.Marker>>(new Map());
  const onMarkerClickRef = useRef(onMarkerClick);
  onMarkerClickRef.current = onMarkerClick;

  const mapped = withCoords(recommendations);

  // Initialise map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      zoomControl: false,
      attributionControl: true,
    });

    L.control.zoom({ position: 'topright' }).addTo(map);

    const tileUrl = theme === 'dark' ? DARK_TILES : LIGHT_TILES;
    const tile = L.tileLayer(tileUrl, { attribution: TILE_ATTR, maxZoom: 18 });
    tile.addTo(map);

    mapRef.current = map;
    tileRef.current = tile;

    return () => {
      map.remove();
      mapRef.current = null;
      tileRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Swap tile layer when theme changes
  useEffect(() => {
    if (!mapRef.current || !tileRef.current) return;
    const map = mapRef.current;
    tileRef.current.remove();
    const tileUrl = theme === 'dark' ? DARK_TILES : LIGHT_TILES;
    const newTile = L.tileLayer(tileUrl, { attribution: TILE_ATTR, maxZoom: 18 });
    newTile.addTo(map);
    tileRef.current = newTile;
  }, [theme]);

  // Build popup HTML for a recommendation
  const buildPopup = useCallback((rec: RankedRecommendation) => {
    const ratingHtml = rec.google_rating != null
      ? `<span style="color:#f59e0b">★</span> ${rec.google_rating.toFixed(1)}${rec.review_count ? ` <span style="opacity:.6">(${rec.review_count.toLocaleString()})</span>` : ''}`
      : '';

    const gradeColor = GRADE_COLORS[rec.hygiene_grade] ?? '#737373';
    const gradeHtml = rec.hygiene_grade !== 'UNKNOWN'
      ? `<span style="color:${gradeColor}">Grade ${rec.hygiene_grade}</span>`
      : '';

    const distHtml = rec.distance_km < 99
      ? `${rec.distance_km.toFixed(1)} km away`
      : '';

    const meta = [gradeHtml, ratingHtml, distHtml].filter(Boolean).join(' &nbsp;·&nbsp; ');

    return `
      <div style="font-family:Geist,DM Sans,system-ui,sans-serif;min-width:200px;max-width:240px">
        <div style="font-weight:600;font-size:14px;margin-bottom:2px">${rec.stall_name}</div>
        <div style="font-size:12px;opacity:.65;margin-bottom:6px">${rec.centre_name}</div>
        ${meta ? `<div style="font-size:11px;margin-bottom:8px">${meta}</div>` : ''}
        <a href="${mapsUrl(rec.stall_name, rec.centre_name)}" target="_blank" rel="noopener noreferrer"
          style="font-size:12px;color:#f59e0b;text-decoration:none;font-weight:500">
          View on Google Maps ↗
        </a>
      </div>
    `;
  }, []);

  // Diff markers: add new, remove stale, update changed
  useEffect(() => {
    if (!mapRef.current) return;
    const map = mapRef.current;
    const prevMarkers = markersRef.current;
    const nextKeys = new Set(mapped.map(markerKey));

    // Remove markers no longer in results
    for (const [key, marker] of prevMarkers) {
      if (!nextKeys.has(key)) {
        map.removeLayer(marker);
        prevMarkers.delete(key);
      }
    }

    if (mapped.length === 0) return;

    const bounds: [number, number][] = [];

    for (const rec of mapped) {
      const key = markerKey(rec);
      const lat = rec.lat!;
      const lng = rec.lng!;
      bounds.push([lat, lng]);

      const isSelected = key === selectedKey;
      const existing = prevMarkers.get(key);

      if (existing) {
        existing.setLatLng([lat, lng]);
        existing.setIcon(makeMarkerIcon(rec, isSelected));
        existing.setPopupContent(buildPopup(rec));
      } else {
        const marker = L.marker([lat, lng], { icon: makeMarkerIcon(rec, isSelected) });
        marker.bindPopup(buildPopup(rec), { maxWidth: 260 });
        marker.on('click', () => {
          onMarkerClickRef.current?.(key);
        });
        marker.addTo(map);
        prevMarkers.set(key, marker);
      }
    }

    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [48, 48], maxZoom: 15 });
    }
  }, [recommendations, selectedKey, buildPopup]); // eslint-disable-line react-hooks/exhaustive-deps

  // When selectedKey changes, open the popup for the selected marker
  useEffect(() => {
    if (!selectedKey || !mapRef.current) return;
    const marker = markersRef.current.get(selectedKey);
    if (marker) {
      marker.openPopup();
      mapRef.current.panTo(marker.getLatLng(), { animate: true, duration: 0.3 });
    }
  }, [selectedKey]);

  if (mapped.length === 0) return null;

  return (
    <div
      ref={containerRef}
      className="w-full h-full rounded-xl overflow-hidden"
      style={{ minHeight: '300px' }}
    />
  );
}
