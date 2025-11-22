import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

interface MapViewProps {
  polygonCoordinates?: string;
}

const MapView = ({ polygonCoordinates }: MapViewProps) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);

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

      // Add fill layer
      map.current!.addLayer({
        id: 'neighborhood-fill',
        type: 'fill',
        source: 'neighborhood',
        paint: {
          'fill-color': '#ffffff',
          'fill-opacity': 0.15
        }
      });

      // Add outline layer
      map.current!.addLayer({
        id: 'neighborhood-outline',
        type: 'line',
        source: 'neighborhood',
        paint: {
          'line-color': '#ffffff',
          'line-width': 2,
          'line-opacity': 0.8
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
