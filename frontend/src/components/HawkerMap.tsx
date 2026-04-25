import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { RankedRecommendation } from '../types';
import { useTheme } from '../context/ThemeContext';

interface HawkerMapProps {
  recommendations: RankedRecommendation[];
}

const LIGHT_TILES = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
const DARK_TILES  = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const TILE_ATTR   = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

function withCoords(recs: RankedRecommendation[]) {
  return recs.filter(r => r.lat != null && r.lng != null);
}

function mapsUrl(stallName: string, centreName: string) {
  return `https://www.google.com/maps/search/?api=1&query=${
    encodeURIComponent(`${stallName} ${centreName} Singapore`)
  }`;
}

function makeMarkerIcon(rank: number): L.DivIcon {
  return L.divIcon({
    className: '',
    iconSize: [34, 34],
    iconAnchor: [17, 34],
    popupAnchor: [0, -36],
    html: `
      <div style="
        width:34px;height:34px;border-radius:50%;
        background:#f59e0b;color:#000;
        display:flex;align-items:center;justify-content:center;
        font-family:Geist,DM Sans,system-ui,sans-serif;
        font-size:13px;font-weight:700;font-variant-numeric:tabular-nums;
        box-shadow:0 2px 8px rgba(0,0,0,0.35);
        border:2px solid rgba(255,255,255,0.6);
      ">${rank}</div>
    `,
  });
}

export function HawkerMap({ recommendations }: HawkerMapProps) {
  const { theme } = useTheme();
  const mapRef = useRef<L.Map | null>(null);
  const tileRef = useRef<L.TileLayer | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

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

  // Add/update markers whenever recommendations change
  useEffect(() => {
    if (!mapRef.current) return;
    const map = mapRef.current;

    // Clear existing markers (except tile layer)
    map.eachLayer(layer => {
      if (layer instanceof L.Marker) map.removeLayer(layer);
    });

    if (mapped.length === 0) return;

    const bounds: [number, number][] = [];

    mapped.forEach(rec => {
      const lat = rec.lat!;
      const lng = rec.lng!;
      bounds.push([lat, lng]);

      const marker = L.marker([lat, lng], { icon: makeMarkerIcon(rec.rank) });

      const ratingHtml = rec.google_rating != null
        ? `<span style="color:#f59e0b">★</span> ${rec.google_rating.toFixed(1)}${rec.review_count ? ` <span style="opacity:.6">(${rec.review_count.toLocaleString()})</span>` : ''}`
        : '';

      const gradeColor: Record<string, string> = {
        A: '#16a34a', B: '#d97706', C: '#dc2626', D: '#dc2626',
      };
      const gradeHtml = rec.hygiene_grade !== 'UNKNOWN'
        ? `<span style="color:${gradeColor[rec.hygiene_grade] ?? '#737373'}">Grade ${rec.hygiene_grade}</span>`
        : '';

      const distHtml = rec.distance_km < 99
        ? `${rec.distance_km.toFixed(1)} km away`
        : '';

      const meta = [gradeHtml, ratingHtml, distHtml].filter(Boolean).join(' &nbsp;·&nbsp; ');

      marker.bindPopup(`
        <div style="font-family:Geist,DM Sans,system-ui,sans-serif;min-width:200px;max-width:240px">
          <div style="font-weight:600;font-size:14px;margin-bottom:2px">${rec.stall_name}</div>
          <div style="font-size:12px;opacity:.65;margin-bottom:6px">${rec.centre_name}</div>
          ${meta ? `<div style="font-size:11px;margin-bottom:8px">${meta}</div>` : ''}
          <a href="${mapsUrl(rec.stall_name, rec.centre_name)}" target="_blank" rel="noopener noreferrer"
            style="font-size:12px;color:#f59e0b;text-decoration:none;font-weight:500">
            View on Google Maps ↗
          </a>
        </div>
      `, { maxWidth: 260 });

      marker.addTo(map);
    });

    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [48, 48], maxZoom: 15 });
    }
  }, [recommendations]); // eslint-disable-line react-hooks/exhaustive-deps

  if (mapped.length === 0) return null;

  return (
    <div
      ref={containerRef}
      className="w-full h-full rounded-xl overflow-hidden"
      style={{ minHeight: '300px' }}
    />
  );
}
