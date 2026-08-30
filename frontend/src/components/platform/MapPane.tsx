import React, { useCallback, useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import {
  Activity, AlertCircle, Fish, Layers, Maximize, MapPin, Navigation, Shield,
} from 'lucide-react';
import { api } from '../../api/client';
import { useOrcaStore } from '../../store/useOrcaStore';

type LayerKey =
  | 'inlet' | 'hazard_corridor' | 'pfz' | 'geofences' | 'grounds' | 'route'
  | 'coverage_line';

const LAYER_META: { key: LayerKey; label: string; Icon: React.ElementType }[] = [
  { key: 'inlet', label: 'Inlet & channel axis', Icon: Layers },
  { key: 'hazard_corridor', label: 'Hazard corridor', Icon: AlertCircle },
  { key: 'pfz', label: 'PFZ advisory points', Icon: Fish },
  { key: 'geofences', label: 'Geofence zones', Icon: Shield },
  { key: 'grounds', label: 'Named fishing grounds', Icon: Activity },
  { key: 'route', label: 'Route corridor', Icon: Navigation },
  { key: 'coverage_line', label: 'Mobile coverage limit', Icon: MapPin },
];

/**
 * Inline raster basemap.
 *
 * Deliberately raster rather than a hosted vector style: a vector style keeps
 * reporting `isStyleLoaded() === false` until its sprites, glyphs and every
 * tile source resolve, so if any of that is slow or blocked the overlays never
 * get added and the map stays blank. An inline style object parses
 * immediately, `style.load` fires straight away, and ORCA's own layers draw
 * whether or not a single tile ever arrives.
 *
 * The background layer sits underneath the tiles, so there is always something
 * to see. Tiles need network; the Coverage tab reports offline as MOCKUP.
 */
const BASEMAP_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      // Standard OSM tiles: free, no API key, no usage gate.
      tiles: [
        'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
        'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
        'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png',
      ],
      tileSize: 256,
      maxzoom: 18,
      attribution: '© OpenStreetMap contributors',
    },
  },
  layers: [
    { id: 'background', type: 'background', paint: { 'background-color': '#cfe3f7' } },
    // NOTE: osm raster layer is NOT added here. It is added programmatically
    // in draw() BEFORE any ORCA layers, guaranteeing it renders underneath.
  ],
};

const TOGGLE_LAYERS: [LayerKey, string[]][] = [
  ['inlet', ['inlet-line', 'inlet-point']],
  ['hazard_corridor', ['hazard_corridor-fill', 'hazard_corridor-line']],
  ['pfz', ['pfz-circle']],
  ['geofences', ['geofences-fill', 'geofences-line']],
  ['grounds', ['grounds-fill', 'grounds-line']],
  ['route', ['route-casing', 'route-line', 'route-points']],
  ['coverage_line', ['coverage_line-line']],
];

function collectCoords(geojson: any, out: [number, number][]) {
  if (!geojson?.features) return;
  const walk = (c: any) => {
    if (typeof c?.[0] === 'number') out.push([c[0], c[1]]);
    else if (Array.isArray(c)) c.forEach(walk);
  };
  geojson.features.forEach((f: any) => walk(f.geometry?.coordinates));
}

export default function MapPane() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const dataRef = useRef<Record<string, any>>({});
  const didFit = useRef(false);

  const [ready, setReady] = useState(false);
  // Bumped whenever a style finishes loading. setStyle() discards every source
  // and layer that was added on top, so the overlays must be re-added.
  const [styleEpoch, setStyleEpoch] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [drawn, setDrawn] = useState(0);
  const [diag, setDiag] = useState<
    { id: string; ok: boolean; vis: string; feats: number }[]>([]);
  const [panelOpen, setPanelOpen] = useState(false);
  const [legendOpen, setLegendOpen] = useState(false);
  const [grounds, setGrounds] = useState<{ ground_id: string; local_name: string }[]>([]);
  const [destGround, setDestGround] = useState('G-QUILON');
  const [routeInfo, setRouteInfo] = useState<
    { dest: string; bearing: number; nm: number; eta: number | null } | null>(null);
  const prevVisible = useRef<Record<string, boolean> | null>(null);
  const routeRef = useRef<{ dest: string; gj: any } | null>(null);
  const fitRef = useRef<() => void>(() => {});
  const [basemap, setBasemap] = useState<'loading' | 'online' | 'offline'>('loading');
  const [visible, setVisible] = useState<Record<LayerKey, boolean>>({
    inlet: true, hazard_corridor: true, pfz: true, geofences: true,
    grounds: false, route: false, coverage_line: true,
  });

  const active = useOrcaStore((s) => s.active);
  const personas = useOrcaStore((s) => s.personas);
  const persona = useOrcaStore((s) => s.persona);
  const context = useOrcaStore((s) => s.context);
  const initGpsWatcher = useOrcaStore((s) => s.initGpsWatcher);
  const userMarkerRef = useRef<maplibregl.Marker | null>(null);
  const pfzMarkersRef = useRef<maplibregl.Marker[]>([]);
  const hasPannedToUser = useRef(false);

  useEffect(() => {
    initGpsWatcher();
  }, [initGpsWatcher]);

  // Handle GPS Marker
  useEffect(() => {
    if (!mapRef.current || !ready) return;
    const map = mapRef.current;
    if (context.user_lat != null && context.user_lon != null) {
      if (!userMarkerRef.current) {
        // Create a custom element for the marker to style it nicely
        const el = document.createElement('div');
        el.className = 'flex h-4 w-4 items-center justify-center rounded-full bg-blue-500 shadow-[0_0_0_2px_white]';
        const inner = document.createElement('div');
        inner.className = 'h-1.5 w-1.5 rounded-full bg-white animate-pulse';
        el.appendChild(inner);

        userMarkerRef.current = new maplibregl.Marker({ element: el })
          .setLngLat([context.user_lon, context.user_lat])
          .setPopup(new maplibregl.Popup({ offset: 10 }).setText('You are here'))
          .addTo(map);
      } else {
        userMarkerRef.current.setLngLat([context.user_lon, context.user_lat]);
      }
    }
  }, [context.user_lat, context.user_lon, ready]);

  useEffect(() => {
    if (mapRef.current && context.user_lat && context.user_lon) {
      if (!hasPannedToUser.current) {
        hasPannedToUser.current = true;
        mapRef.current.flyTo({ center: [context.user_lon, context.user_lat], zoom: 11 });
      }
    }
  }, [context.user_lat, context.user_lon]);

  // Handle PFZ Highlights
  useEffect(() => {
    if (!mapRef.current || !ready) return;
    const map = mapRef.current;
    
    // Clear old markers
    pfzMarkersRef.current.forEach(m => m.remove());
    pfzMarkersRef.current = [];
      if (active?.intent_result?.kind === 'nearest_pfz' && active.intent_result.points) {
        const bounds = new maplibregl.LngLatBounds();
        let added = false;
        
        active.intent_result.points.forEach((pfz: any, idx: number) => {
          const el = document.createElement('div');
          // Top PFZ gets a bouncing bigger marker, others get standard
          const isTop = idx === 0;
          el.className = `flex items-center justify-center rounded-full bg-emerald-600 shadow-md border-2 border-white text-white font-bold text-[10px] ${isTop ? 'h-7 w-7 animate-bounce' : 'h-5 w-5'}`;
          el.innerHTML = `${idx + 1}`;

          const marker = new maplibregl.Marker({ element: el })
            .setLngLat([pfz.lon, pfz.lat])
            .setPopup(new maplibregl.Popup({ offset: 15 }).setHTML(`
              <div class="text-xs p-1">
                <strong>PFZ ${idx + 1}</strong><br/>
                Depth: ${pfz.depth_m}m<br/>
                Confidence: ${(pfz.confidence * 100).toFixed(0)}%
              </div>
            `))
            .addTo(map);
            
          pfzMarkersRef.current.push(marker);
          bounds.extend([pfz.lon, pfz.lat]);
          added = true;
        });

        // Frame the PFZ points and the user's location
        if (added) {
          if (context.user_lat && context.user_lon) {
            bounds.extend([context.user_lon, context.user_lat]);
          }
          map.fitBounds(bounds, { padding: 80, maxZoom: 12, duration: 800 });
        }
      }
    }, [active, ready, context.user_lat, context.user_lon]);

  // FR-21: the backend reports which layers the answer actually used.
  useEffect(() => {
    if (!active) return;
    setVisible((v) => {
      const next = { ...v };
      for (const key of active.layers) if (key in next) next[key as LayerKey] = true;
      return next;
    });
  }, [active]);

  useEffect(() => {
    if (mapRef.current || !containerRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: BASEMAP_STYLE,
      center: [78.9629, 20.5937],
      zoom: 4,
      // Expanded to include the whole India map
      maxBounds: [[68.0, 6.5], [97.5, 37.5]],
      minZoom: 3.5,
      maxZoom: 16,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    map.addControl(new maplibregl.ScaleControl({ maxWidth: 100, unit: 'metric' }));
    mapRef.current = map;
    if (import.meta.env.DEV) (window as any).__orcaMap = map;

    const onError = (e: any) => {
      // Tile fetches failing is survivable - the overlays are the point - so
      // note it and carry on rather than blanking the pane.
      const msg = String(e?.error?.message ?? e?.error ?? '');
      if (msg.includes('tile') || msg.includes('Failed to fetch')) {
        setBasemap('offline');
      }
    };
    map.on('error', onError);
    // Fires as soon as the inline style is parsed - no tiles required.
    map.on('style.load', () => {
      setBasemap((b) => (b === 'offline' ? b : 'online'));
      setStyleEpoch((n) => n + 1);
    });

    // A map built before its container has final layout renders blank until
    // something forces a resize - a common cause of an empty canvas inside a
    // flex/grid pane. Watch the box and tell the map whenever it changes.
    const ro = new ResizeObserver(() => map.resize());
    ro.observe(containerRef.current);

    return () => {
      ro.disconnect();
      map.off('error', onError);
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    api.grounds().then((d) => setGrounds(d.grounds)).catch(() => setGrounds([]));
  }, []);

  /** Frame a single layer, so switching one on always brings it into view. */
  const fitToLayer = useCallback((key: string) => {
    const map = mapRef.current;
    const gj = dataRef.current[key];
    if (!map || !gj) return;
    const coords: [number, number][] = [];
    collectCoords(gj, coords);
    if (!coords.length) return;
    const b = coords.reduce(
      (acc, c) => acc.extend(c),
      new maplibregl.LngLatBounds(coords[0], coords[0]),
    );
    map.fitBounds(b, { padding: 80, maxZoom: 12, duration: 700 });
  }, []);

  /** Frame layers relevant to the current query, plus GPS. */
  const fitToData = useCallback(() => {
    const map = mapRef.current;
    if (!map) return;
    const coords: [number, number][] = [];
    const store = useOrcaStore.getState();
    
    // Frame the layers relevant to the active query, or defaults if none
    const relevantLayers = store.active 
      ? store.active.layers 
      : ['inlet', 'hazard_corridor', 'pfz'];

    for (const key of relevantLayers) {
      if (visible[key as LayerKey] && dataRef.current[key]) {
        collectCoords(dataRef.current[key], coords);
      }
    }
    
    // Only include user location if the query explicitly requested it, or if nothing else is visible.
    // Otherwise, framing a user in Bangalore + the inlet in Kerala zooms out the map to show all of South India!
    if (store.context.user_lat != null && store.context.user_lon != null) {
      if (store.active?.intent === 'location' || !coords.length) {
        coords.push([store.context.user_lon, store.context.user_lat]);
      }
    }

    // Fallback if nothing relevant is visible
    if (!coords.length) {
      for (const [key, on] of Object.entries(visible)) {
        if (on && dataRef.current[key]) collectCoords(dataRef.current[key], coords);
      }
    }

    if (!coords.length) return;
    const b = coords.reduce(
      (acc, c) => acc.extend(c),
      new maplibregl.LngLatBounds(coords[0], coords[0]),
    );
    map.fitBounds(b, { padding: 60, maxZoom: 12, duration: 600 });
  }, [visible]);

  useEffect(() => { fitRef.current = fitToData; }, [fitToData]);

  const draw = useCallback(async () => {
    const map = mapRef.current;
    if (!map) return;
    // Do NOT gate on isStyleLoaded(): it stays false until every source, sprite
    // and glyph resolves, so one blocked request would leave the map blank
    // forever. getStyle() returning a spec means addSource/addLayer are legal,
    // which is all this needs.
    if (!map.getStyle()) {
      window.setTimeout(() => { void draw(); }, 200);
      return;
    }
    setReady(true);
    try {
      const data = await api.mapLayers(active?.verdict, active?.index_value, context.user_lat, context.user_lon);

      // The route corridor is a real endpoint call, not a static layer. It is
      // cached against the chosen destination: a redraw triggered by some other
      // layer's toggle must not refetch it, and must never blank it.
      let route: any = routeRef.current?.gj
        ?? { type: 'FeatureCollection', features: [] as any[] };
      const needRoute = visible.route && routeRef.current?.dest !== destGround;
      if (needRoute) {
        try {
          const r = await api.route(destGround);
          setRouteInfo({ dest: r.destination.local_name, bearing: r.bearing_deg,
                         nm: r.distance_nm, eta: r.eta_hours });
          const line = r.waypoints.map((w: any) => [w.lon, w.lat]);
          route = {
            type: 'FeatureCollection',
            features: [
              {
                type: 'Feature',
                properties: {
                  kind: 'route', destination: r.destination.local_name,
                  bearing_deg: r.bearing_deg, distance_nm: r.distance_nm,
                  eta_hours: r.eta_hours, status: r.status, caveat: r.caveat,
                },
                geometry: { type: 'LineString', coordinates: line },
              },
              ...r.waypoints.map((w: any, i: number) => ({
                type: 'Feature',
                properties: { kind: 'waypoint', n: i, distance_km: w.distance_km },
                geometry: { type: 'Point', coordinates: [w.lon, w.lat] },
              })),
            ],
          };
          routeRef.current = { dest: destGround, gj: route };
        } catch {
          // Keep whatever corridor was already drawn rather than blanking it.
          route = routeRef.current?.gj
            ?? { type: 'FeatureCollection', features: [] };
        }
      }

      dataRef.current = { ...data, route };
      setError(null);

      const upsert = (id: string, geojson: any) => {
        const src = map.getSource(id) as maplibregl.GeoJSONSource | undefined;
        if (src) src.setData(geojson);
        else map.addSource(id, { type: 'geojson', data: geojson });
      };
      for (const id of ['coverage_line', 'grounds', 'hazard_corridor',
        'route', 'pfz', 'inlet']) {
        upsert(id, id === 'route' ? route : data[id]);
      }
      
      // (Hardcoded test removed)

      const add = (spec: maplibregl.LayerSpecification) => {
        if (!map.getLayer(spec.id)) map.addLayer(spec);
      };

      // Add the raster basemap FIRST so it renders BELOW all ORCA layers.
      // This was previously in BASEMAP_STYLE but MapLibre's style-defined layers
      // always render above programmatically-added layers, hiding our overlays.
      // add({
      //   id: 'osm', type: 'raster', source: 'osm',
      //   paint: { 'raster-opacity': 0.65 },
      // } as any);

      add({
        id: 'grounds-fill', type: 'fill', source: 'grounds',
        paint: { 'fill-color': '#0ea5e9', 'fill-opacity': 0.12 },
      });
      add({
        id: 'grounds-line', type: 'line', source: 'grounds',
        paint: { 'line-color': '#0284c7', 'line-width': 1, 'line-dasharray': [2, 2] },
      });
      add({
        id: 'geofences-fill', type: 'fill', source: 'geofences',
        paint: { 'fill-color': ['get', 'colour'], 'fill-opacity': 0.35 },
      });
      add({
        id: 'geofences-line', type: 'line', source: 'geofences',
        paint: { 'line-color': ['get', 'colour'], 'line-width': 3 },
      });
      add({
        id: 'hazard_corridor-fill', type: 'fill', source: 'hazard_corridor',
        paint: { 'fill-color': ['get', 'colour'], 'fill-opacity': 0.45 },
      });
      add({
        id: 'hazard_corridor-line', type: 'line', source: 'hazard_corridor',
        paint: { 'line-color': ['get', 'colour'], 'line-width': 2 },
      });
      add({
        id: 'coverage_line-line', type: 'line', source: 'coverage_line',
        paint: { 'line-color': '#7c3aed', 'line-width': 2, 'line-dasharray': [3, 2] },
      });
      // Casing first, so the corridor reads against water, land or ferry lines.
      add({
        id: 'route-casing', type: 'line', source: 'route',
        filter: ['==', ['get', 'kind'], 'route'],
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: { 'line-color': '#431407', 'line-width': 8, 'line-opacity': 0.9 },
      });
      add({
        id: 'route-line', type: 'line', source: 'route',
        filter: ['==', ['get', 'kind'], 'route'],
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: { 'line-color': '#f97316', 'line-width': 4, 'line-opacity': 1 },
      });
      add({
        id: 'route-points', type: 'circle', source: 'route',
        filter: ['==', ['get', 'kind'], 'waypoint'],
        paint: {
          'circle-radius': 5, 'circle-color': '#f97316',
          'circle-stroke-color': '#431407', 'circle-stroke-width': 2,
        },
      });
      add({
        id: 'pfz-circle', type: 'circle', source: 'pfz',
        paint: {
          'circle-radius': 5, 'circle-color': '#059669',
          'circle-stroke-color': '#ffffff', 'circle-stroke-width': 1.5,
        },
      });
      add({
        id: 'inlet-line', type: 'line', source: 'inlet',
        filter: ['==', ['get', 'kind'], 'channel_axis'],
        paint: { 'line-color': '#0f172a', 'line-width': 3 },
      });
      add({
        id: 'inlet-point', type: 'circle', source: 'inlet',
        filter: ['==', ['get', 'kind'], 'inlet'],
        paint: {
          'circle-radius': 8, 'circle-color': '#0f172a',
          'circle-stroke-color': '#ffffff', 'circle-stroke-width': 3,
        },
      });

      for (const id of ['geofences-fill', 'pfz-circle', 'inlet-point', 'grounds-fill',
        'hazard_corridor-fill', 'route-line', 'route-casing']) {
        if ((map as any)[`__pop_${id}`]) continue;
        (map as any)[`__pop_${id}`] = true;
        map.on('click', id, (e: any) => {
          const f = e.features?.[0];
          if (!f) return;
          const rows = Object.entries(f.properties ?? {})
            .filter(([k]) => !k.startsWith('_') && k !== 'colour')
            .map(([k, v]) => `<div><b>${k}</b>: ${v}</div>`).join('');
          new maplibregl.Popup({ closeButton: true })
            .setLngLat(e.lngLat)
            .setHTML(`<div style="font:12px system-ui;max-width:18rem">${rows}</div>`)
            .addTo(map);
        });
        map.on('mouseenter', id, () => { map.getCanvas().style.cursor = 'pointer'; });
        map.on('mouseleave', id, () => { map.getCanvas().style.cursor = ''; });
      }

      // Frame the data once. Without this the default viewport shows only the
      // inlet dot: the PFZ points and zones sit well outside it.
      if (!didFit.current) {
        didFit.current = true;
        window.setTimeout(() => fitRef.current(), 150);
      }

      const allIds = TOGGLE_LAYERS.flatMap(([, ids]) => ids);

      // No moveLayer hacks needed: the osm raster is now added programmatically
      // BEFORE all ORCA layers in add() above, so the rendering order is correct
      // by construction: background → osm → fills → lines → points.
      map.triggerRepaint();

      setDrawn(allIds.filter((id) => !!map.getLayer(id)).length);

      // Per-layer state: does the layer exist, is it visible, and does its
      // source actually hold features? Guessing at a blank map from the outside
      // wastes far more time than reading it off the screen.
      window.setTimeout(() => {
        const rows = allIds.map((id) => {
          const layer: any = map.getLayer(id);
          let feats = 0;
          try {
            const srcId: string | undefined = layer && (layer.source ?? layer.sourceId);
            const gj = srcId ? dataRef.current[srcId] : null;
            feats = gj?.features?.length ?? 0;
          } catch { feats = -1; }
          return {
            id,
            ok: !!layer,
            vis: layer ? String(map.getLayoutProperty(id, 'visibility') ?? 'visible') : '-',
            feats,
          };
        });
        setDiag(rows);
        // Also on the console, so it can be read without the panel in the way.
        // eslint-disable-next-line no-console
        console.table(rows);
        // eslint-disable-next-line no-console
        console.log("MapLibre layer order:", map.getStyle()?.layers.map(l => l.id));
      }, 300);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Map data unavailable');
      // Adding layers can fail if the style was swapped mid-flight. Retry once.
      window.setTimeout(() => { void draw(); }, 500);
    }
  }, [active, visible.route, destGround, styleEpoch, context.user_lat, context.user_lon]);

  useEffect(() => { void draw(); }, [draw]);

  // Turning a layer on and seeing nothing - because its features sit outside
  // the current viewport - reads as a broken layer. Frame whatever was just
  // switched on.
  useEffect(() => {
    if (!ready) return;
    const prev = prevVisible.current;
    prevVisible.current = { ...visible };
    if (!prev) return;
    const turnedOn = Object.keys(visible).find((k) => visible[k as LayerKey] && !prev[k]);
    if (turnedOn) window.setTimeout(() => fitToLayer(turnedOn), 200);
  }, [visible, ready, fitToLayer]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    for (const [key, ids] of TOGGLE_LAYERS) {
      for (const id of ids) {
        if (map.getLayer(id)) {
          map.setLayoutProperty(id, 'visibility', visible[key] ? 'visible' : 'none');
        }
      }
    }
  }, [visible, ready, active, styleEpoch]);

  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="h-full w-full" />

      <div className={`absolute left-2 top-2 z-10 rounded-lg border border-slate-200
        bg-white/95 shadow-md backdrop-blur ${panelOpen ? 'w-48 p-1.5' : 'p-1'}`}>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setPanelOpen((o) => !o)}
            title={panelOpen ? 'Hide layer controls' : 'Show layer controls'}
            className="flex flex-1 items-center gap-1 rounded px-1 py-0.5 text-[10px]
              font-bold uppercase tracking-wide text-slate-500 hover:bg-slate-100"
          >
            <Layers className="h-3.5 w-3.5" aria-hidden />
            {panelOpen && 'Layers'}
            <Maximize className={`h-3 w-3 ${panelOpen ? 'rotate-0' : ''}`} aria-hidden />
          </button>
          {panelOpen && (
            <button
              onClick={() => {
                if (context.user_lat && context.user_lon) {
                  mapRef.current?.flyTo({ center: [context.user_lon, context.user_lat], zoom: 11, duration: 800 });
                } else {
                  mapRef.current?.flyTo({ center: [78.9629, 20.5937], zoom: 4, duration: 800 }); // Center of India
                }
              }}
              title="My Location"
              className="rounded border border-slate-300 px-1.5 py-0.5 text-[10px]
                font-semibold text-slate-600 hover:bg-slate-100"
            >
              MY LOCATION
            </button>
          )}
          {panelOpen && (
            <button
              onClick={fitToData}
              title="Zoom to fit everything switched on"
              className="rounded border border-slate-300 px-1.5 py-0.5 text-[10px]
                font-semibold text-slate-600 hover:bg-slate-100"
            >
              Fit
            </button>
          )}
        </div>
        {panelOpen && (
        <>
        <div className="mt-1 space-y-px">
          {LAYER_META.map(({ key, label, Icon }) => {
            const on = visible[key];
            return (
              <button
                key={key}
                onClick={() => setVisible((v) => ({ ...v, [key]: !v[key] }))}
                aria-pressed={on}
                className={`flex w-full items-center gap-1.5 rounded px-1.5 py-1
                  text-[11px] ${on ? 'bg-sky-100 font-medium text-sky-800'
                    : 'text-slate-600 hover:bg-slate-100'}`}
              >
                <Icon className="h-3.5 w-3.5" aria-hidden />
                <span className="flex-1 text-left">{label}</span>
              </button>
            );
          })}
        </div>

        {visible.route && (
          <div className="mt-1.5 rounded-lg border border-indigo-200 bg-indigo-50 p-2">
            <label className="block text-[10px] font-bold uppercase tracking-wide
              text-indigo-900">
              Destination ground
            </label>
            <select
              value={destGround}
              onChange={(e) => setDestGround(e.target.value)}
              className="mt-1 w-full rounded border border-indigo-300 bg-white px-1.5
                py-1 text-[11px] text-slate-800 outline-none focus:ring-2
                focus:ring-indigo-500"
            >
              {grounds.map((g) => (
                <option key={g.ground_id} value={g.ground_id}>{g.local_name}</option>
              ))}
            </select>
            {routeInfo && (
              <dl className="mt-1.5 grid grid-cols-3 gap-1 text-[10px] text-indigo-900">
                <div>
                  <dt className="text-indigo-500">Bearing</dt>
                  <dd className="font-mono font-bold">{routeInfo.bearing}°</dd>
                </div>
                <div>
                  <dt className="text-indigo-500">Distance</dt>
                  <dd className="font-mono font-bold">{routeInfo.nm} nm</dd>
                </div>
                <div>
                  <dt className="text-indigo-500">ETA</dt>
                  <dd className="font-mono font-bold">
                    {routeInfo.eta != null ? `${routeInfo.eta} h` : '—'}
                  </dd>
                </div>
              </dl>
            )}
            <p className="mt-1 text-[9px] leading-snug text-indigo-700">
              Planning ashore only — not a navigation instruction.
            </p>
          </div>
        )}
        <details className="mt-1.5 px-1.5 text-[10px] text-slate-400">
          <summary className="cursor-pointer">
            {drawn} overlays drawn · basemap {basemap}
          </summary>
          <table className="mt-1 w-full text-[9px]">
            <tbody>
              {diag.map((d) => (
                <tr key={d.id} className={d.ok && d.vis === 'visible' && d.feats > 0
                  ? 'text-slate-500' : 'text-red-600'}>
                  <td className="pr-1">{d.id.replace('-', ' ')}</td>
                  <td className="pr-1">{d.ok ? d.vis : 'MISSING'}</td>
                  <td className="text-right">{d.feats}f</td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
        {basemap === 'offline' && (
          <p className="mt-1 rounded bg-amber-50 px-1.5 py-1 text-[9px] text-amber-900">
            Basemap tiles unreachable — ORCA layers still drawn.
          </p>
        )}
        </>
        )}
      </div>

      {legendOpen ? (
        <div className="absolute bottom-8 right-2 z-10 rounded-lg border border-slate-200
          bg-white/95 px-2 py-1.5 text-[10px] shadow-md backdrop-blur">
          <button
            onClick={() => setLegendOpen(false)}
            className="mb-0.5 flex w-full items-center justify-between gap-3 font-bold
              text-slate-700 hover:text-slate-900"
          >
            Legend <span aria-hidden>×</span>
          </button>
          <LegendRow colour="#0f172a" label="Inlet & channel axis (250°)" />
          <LegendRow
            colour={active?.verdict === 'SAFE' ? '#059669'
              : active?.verdict === 'MARGINAL' ? '#d97706'
                : active ? '#dc2626' : '#64748b'}
            label={`Hazard corridor${active ? ` · ${active.verdict.replace(/_/g, ' ')}` : ''}`}
          />
          <LegendRow colour="#059669" label="PFZ points" />
          <LegendRow colour="#dc2626" label="Geofence zones" />
          <LegendRow colour="#f97316" label="Route corridor" />
          <LegendRow colour="#7c3aed" label="Coverage limit (~15 km)" />
        </div>
      ) : (
        <button
          onClick={() => setLegendOpen(true)}
          className="absolute bottom-2 left-2 z-10 rounded-lg border border-slate-200
            bg-white/95 px-2 py-1 text-[10px] font-bold text-slate-600 shadow-md
            backdrop-blur hover:bg-white"
        >
          Legend
        </button>
      )}

      {error && (
        <div className="absolute inset-x-3 top-3 z-20 rounded-lg border border-red-300
          bg-red-50 p-2 text-xs text-red-900">
          Map data unavailable: {error}
        </div>
      )}
      {!ready && (
        <div className="pointer-events-none absolute inset-0 flex items-center
          justify-center bg-slate-100/80 text-sm text-slate-500">
          Loading map…
        </div>
      )}
    </div>
  );
}

function LegendRow({ colour, label }: { colour: string; label: string }) {
  return (
    <div className="mt-1 flex items-center gap-1.5 text-slate-600">
      <span className="h-2.5 w-2.5 rounded-sm" style={{ background: colour }} />
      {label}
    </div>
  );
}
