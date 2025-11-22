import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

interface MapViewProps {
  polygonCoordinates?: string;
  activeAction?: any;
}

const MapView = ({ polygonCoordinates, activeAction }: MapViewProps) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);

  // Handle Active Action (Lines or POIs)
  useEffect(() => {
    if (!map.current || !activeAction) return;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // Clear existing lines
    if (map.current.getLayer('distance-line')) map.current.removeLayer('distance-line');
    if (map.current.getSource('distance-line')) map.current.removeSource('distance-line');

    if (activeAction.type === 'line' && activeAction.data) {
      const { start, end, color } = activeAction.data;
      
      // Add Line Source
      map.current.addSource('distance-line', {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: {
            type: 'LineString',
            coordinates: [start, end]
          }
        }
      });

      // Add Line Layer
      map.current.addLayer({
        id: 'distance-line',
        type: 'line',
        source: 'distance-line',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': color || '#ff0000',
          'line-width': 4,
          'line-dasharray': [2, 1]
        }
      });

      // Fit bounds to show line
      const bounds = new mapboxgl.LngLatBounds();
      bounds.extend(start);
      bounds.extend(end);
      map.current.fitBounds(bounds, { padding: 50 });
    } 
    else if ((activeAction.type === 'layer' || activeAction.type === 'poi_layer') && activeAction.locations) {
      // Add Markers for POIs
      activeAction.locations.forEach((loc: any) => {
        const el = document.createElement('div');
        el.className = 'marker';
        el.style.backgroundColor = '#3b82f6';
        el.style.width = '12px';
        el.style.height = '12px';
        el.style.borderRadius = '50%';
        el.style.border = '2px solid white';
        el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.3)';

        const marker = new mapboxgl.Marker(el)
          .setLngLat([loc.lon, loc.lat])
          .setPopup(new mapboxgl.Popup({ offset: 25 }).setText(loc.name))
          .addTo(map.current!);
        
        markersRef.current.push(marker);
      });
      
      // Fit bounds to show all markers + polygon center
      if (activeAction.locations.length > 0) {
         const bounds = new mapboxgl.LngLatBounds();
         activeAction.locations.forEach((loc: any) => bounds.extend([loc.lon, loc.lat]));
         map.current.fitBounds(bounds, { padding: 50, maxZoom: 14 });
      }
    }

  }, [activeAction]);

  useEffect(() => {
    if (!mapContainer.current) return;

    // Initialize map with LA center
    mapboxgl.accessToken = 'pk.eyJ1Ijoibmlyb2dvIiwiYSI6ImNtZ2szcXBlcDBxcTEydnI0a3F0NXNqaHIifQ.XkP8QTwkw0ia-YLlma59GQ';
    
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/outdoors-v12',
      center: [-118.2437, 34.0522], // Los Angeles
      zoom: 11,
      pitch: 0,
    });

    // Add navigation controls
    map.current.addControl(
      new mapboxgl.NavigationControl({
        visualizePitch: true,
      }),
      'top-right'
    );

    // Add polygon when map loads
    map.current.on('load', () => {
      if (!polygonCoordinates || !map.current) return;

      // Parse polygon coordinates from string
      const coordsMatch = polygonCoordinates.match(/POLYGON \(\((.*?)\)\)/);
      if (!coordsMatch) return;

      const coordPairs = coordsMatch[1].split(', ');
      const coordinates = coordPairs.map(pair => {
        const [lng, lat] = pair.trim().split(' ').map(Number);
        return [lng, lat];
      });

      // Add source for polygon
      map.current!.addSource('neighborhood', {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: {
            type: 'Polygon',
            coordinates: [coordinates]
          },
          properties: {}
        }
      });

      // Add glow layer (under outline) for subtle glassy aura
      map.current!.addLayer({
        id: 'neighborhood-glow',
        type: 'line',
        source: 'neighborhood',
        paint: {
          'line-color': '#0b3d91',
          'line-width': 8,
          'line-opacity': 0.25,
          'line-blur': 6
        }
      });

      // Add fill layer (subtle blue tint inside perimeter)
      map.current!.addLayer({
        id: 'neighborhood-fill',
        type: 'fill',
        source: 'neighborhood',
        paint: {
          'fill-color': '#0b3d91',
          'fill-opacity': 0.18
        }
      });

      // Add outline layer (crisp edge on top)
      map.current!.addLayer({
        id: 'neighborhood-outline',
        type: 'line',
        source: 'neighborhood',
        paint: {
          'line-color': '#0b3d91',
          'line-width': 3,
          'line-opacity': 0.9,
          'line-blur': 0.7
        }
      });

      // Calculate bounds and fit map
      const bounds = new mapboxgl.LngLatBounds();
      coordinates.forEach(coord => bounds.extend(coord as [number, number]));
      map.current!.fitBounds(bounds, { padding: 50 });
    });

    // Cleanup
    return () => {
      map.current?.remove();
    };
  }, [polygonCoordinates]);

  return <div ref={mapContainer} className="w-full h-full" />;
};

export default MapView;
