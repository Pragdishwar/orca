import React, { useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Layers, Activity, Shield, Fish, Navigation, AlertCircle } from 'lucide-react';

export default function MapPane() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  
  const [layers, setLayers] = useState({
    inletGeometry: true,
    waveHazard: false,
    pfz: false,
    geofence: true,
    heatmap: false,
    route: false,
    boundary: false,
  });

  useEffect(() => {
    if (map.current || !mapContainer.current) return;
    
    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center: [76.786, 8.636], // Muthalapozhi Inlet
      zoom: 13
    });

    map.current.on('load', () => {
      // Mocking layer additions would go here
    });

  }, []);

  const toggleLayer = (key: keyof typeof layers) => {
    setLayers({ ...layers, [key]: !layers[key] });
    // In real implementation: map.current.setLayoutProperty(key, 'visibility', !layers[key] ? 'visible' : 'none')
  };

  return (
    <div className="relative h-full w-full bg-slate-100 flex flex-col">
      {/* Layer Controls - Overlay */}
      <div className="absolute top-4 left-4 z-10 bg-white/90 backdrop-blur-sm p-2 rounded-xl shadow-lg border border-gray-200 w-56">
        <h4 className="text-xs font-bold text-gray-500 uppercase mb-2 px-2">Map Controls</h4>
        <div className="space-y-1">
          <button onClick={() => toggleLayer('inletGeometry')} className={`w-full flex items-center text-xs p-2 rounded ${layers.inletGeometry ? 'bg-blue-100 text-blue-700 font-medium' : 'hover:bg-gray-100 text-gray-600'}`}>
            <Layers className="w-3 h-3 mr-2" /> Inlet & Channel Axis
          </button>
          <button onClick={() => toggleLayer('waveHazard')} className={`w-full flex items-center text-xs p-2 rounded ${layers.waveHazard ? 'bg-red-100 text-red-700 font-medium' : 'hover:bg-gray-100 text-gray-600'}`}>
            <AlertCircle className="w-3 h-3 mr-2" /> Wave Hazard Corridor
          </button>
          <button onClick={() => toggleLayer('pfz')} className={`w-full flex items-center text-xs p-2 rounded ${layers.pfz ? 'bg-emerald-100 text-emerald-700 font-medium' : 'hover:bg-gray-100 text-gray-600'}`}>
            <Fish className="w-3 h-3 mr-2" /> PFZ Advisory Points
          </button>
          <button onClick={() => toggleLayer('geofence')} className={`w-full flex items-center text-xs p-2 rounded ${layers.geofence ? 'bg-amber-100 text-amber-700 font-medium' : 'hover:bg-gray-100 text-gray-600'}`}>
            <Shield className="w-3 h-3 mr-2" /> Geofence (IMBL/MPA)
          </button>
          <button onClick={() => toggleLayer('heatmap')} className={`w-full flex items-center text-xs p-2 rounded ${layers.heatmap ? 'bg-purple-100 text-purple-700 font-medium' : 'hover:bg-gray-100 text-gray-600'}`}>
            <Activity className="w-3 h-3 mr-2" /> Chl/SST Heatmap
          </button>
          <button onClick={() => toggleLayer('route')} className={`w-full flex items-center text-xs p-2 rounded ${layers.route ? 'bg-indigo-100 text-indigo-700 font-medium' : 'hover:bg-gray-100 text-gray-600'}`}>
            <Navigation className="w-3 h-3 mr-2" /> Optimal Route Corridor
          </button>
          <button onClick={() => toggleLayer('boundary')} className={`w-full flex items-center text-xs p-2 rounded ${layers.boundary ? 'bg-slate-200 text-slate-800 font-medium' : 'hover:bg-gray-100 text-gray-600'}`}>
            <MapPin className="w-3 h-3 mr-2" /> Coastal Coverage Limit
          </button>
        </div>
      </div>

      {/* Map Container */}
      <div ref={mapContainer} className="flex-1 w-full" />
    </div>
  );
}

// MapPin icon defined locally for boundary layer since it's missing from import
const MapPin = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
);
