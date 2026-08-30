-- Supabase Schema Migration

CREATE TABLE public.boats (
    boat_id TEXT PRIMARY KEY,
    hull_class TEXT NOT NULL,
    length_m NUMERIC NOT NULL,
    engine_hp INTEGER NOT NULL,
    crew INTEGER NOT NULL,
    home_harbour TEXT NOT NULL,
    threshold_bucket TEXT NOT NULL
);

CREATE TABLE public.named_grounds (
    ground_id TEXT PRIMARY KEY,
    local_name TEXT NOT NULL,
    centroid_lat NUMERIC NOT NULL,
    centroid_lon NUMERIC NOT NULL,
    radius_km NUMERIC NOT NULL
);

CREATE TABLE public.geofence_zones (
    zone_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    buffer_km NUMERIC NOT NULL,
    provenance TEXT NOT NULL,
    geojson JSONB NOT NULL
);

-- Insert Seed Data for Boats
INSERT INTO public.boats (boat_id, hull_class, length_m, engine_hp, crew, home_harbour, threshold_bucket) VALUES
('B001', 'FRP_SMALL', 9.0, 25, 4, 'Muthalapozhi', 'FRP_SMALL'),
('B002', 'TRAWLER_MED', 12.0, 90, 6, 'Muthalapozhi', 'TRAWLER_MED'),
('B003', 'PLYWOOD_CANOE', 6.2, 9, 3, 'Muthalapozhi', 'PLYWOOD_CANOE'),
('B004', 'FRP_SMALL', 8.4, 15, 3, 'Muthalapozhi', 'FRP_SMALL'),
('B005', 'TRAWLER_DEEP', 19.5, 180, 8, 'Muthalapozhi', 'TRAWLER_DEEP');

-- Insert Seed Data for Named Grounds
INSERT INTO public.named_grounds (ground_id, local_name, centroid_lat, centroid_lon, radius_km) VALUES
('G-MUTH-NEAR', 'Muthalapozhi Nearshore', 8.6480, 76.7350, 4.0),
('G-PARA', 'Paravur Shelf', 8.7600, 76.6600, 6.0),
('G-QUILON', 'Quilon Bank', 8.8500, 76.3000, 18.0),
('G-WADGE', 'Wadge Bank', 7.9500, 77.3000, 22.0),
('G-TVM-DEEP', 'Trivandrum Deep', 8.3000, 76.5000, 14.0),
('G-ANCHU', 'Anchuthengu Grounds', 8.6800, 76.7000, 5.0),
('G-VIZH', 'Vizhinjam Offshore', 8.3700, 76.9200, 9.0);

-- Insert Seed Data for Geofences
INSERT INTO public.geofence_zones (zone_id, name, type, buffer_km, provenance, geojson) VALUES
('Z-IMBL-01', 'India-Sri Lanka IMBL approach', 'IMBL', 5.0, 'LIVE_DATABASE', '{"type": "Polygon", "coordinates": [[[77.10, 7.60], [77.80, 7.60], [77.80, 7.95], [77.10, 7.95], [77.10, 7.60]]]}'),
('Z-MPA-01', 'Vizhinjam Reef Marine Protected Area', 'MPA', 2.0, 'LIVE_DATABASE', '{"type": "Polygon", "coordinates": [[[76.86, 8.32], [76.98, 8.32], [76.98, 8.42], [76.86, 8.42], [76.86, 8.32]]]}'),
('Z-SENS-01', 'Anchuthengu Turtle Nesting Belt', 'SENSITIVE', 2.0, 'LIVE_DATABASE', '{"type": "Polygon", "coordinates": [[[76.68, 8.63], [76.76, 8.63], [76.76, 8.74], [76.68, 8.74], [76.68, 8.63]]]}'),
('Z-REST-01', 'Vizhinjam Port Approach Channel', 'RESTRICTED', 1.5, 'LIVE_DATABASE', '{"type": "Polygon", "coordinates": [[[76.97, 8.36], [77.05, 8.36], [77.05, 8.41], [76.97, 8.41], [76.97, 8.36]]]}'),
('Z-REST-02', 'Muthalapozhi Harbour Mouth Exclusion', 'RESTRICTED', 0.5, 'LIVE_DATABASE', '{"type": "Polygon", "coordinates": [[[76.780, 8.628], [76.792, 8.628], [76.792, 8.644], [76.780, 8.644], [76.780, 8.628]]]}'),
('Z-SENS-02', 'Quilon Bank Trawl Ban Belt', 'SENSITIVE', 3.0, 'LIVE_DATABASE', '{"type": "Polygon", "coordinates": [[[76.20, 8.78], [76.42, 8.78], [76.42, 8.94], [76.20, 8.94], [76.20, 8.78]]]}');

-- Allow anon read access (Row Level Security)
ALTER TABLE public.boats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.named_grounds ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.geofence_zones ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read on boats" ON public.boats FOR SELECT USING (true);
CREATE POLICY "Allow public read on named_grounds" ON public.named_grounds FOR SELECT USING (true);
CREATE POLICY "Allow public read on geofence_zones" ON public.geofence_zones FOR SELECT USING (true);
