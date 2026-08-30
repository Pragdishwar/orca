/**
 * Typed access to the ORCA backend.
 *
 * Every panel in the app reads through here, so nothing renders a number the
 * backend did not compute. If an endpoint fails, the caller shows an error
 * state - it never falls back to a plausible-looking constant.
 */

export const API_URL =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') ||
  'http://localhost:8000';

/**
 * Shared demo token for write endpoints (SRS 7.4).
 *
 * This is not a secret and is not authentication: it ships in the bundle and
 * anyone can read it out of devtools. It exists to stop casual and accidental
 * writes against a running demo. Real access control needs a server-side
 * identity provider - see the Coverage tab.
 */
const DEMO_TOKEN =
  (import.meta.env.VITE_ORCA_TOKEN as string | undefined) || 'orca-demo-token';

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        'X-ORCA-Token': DEMO_TOKEN,
        ...(init?.headers || {}),
      },
    });
  } catch {
    throw new ApiError(`Cannot reach the ORCA engine at ${API_URL}.`, 0);
  }
  const body = await res.text();
  let parsed: any = null;
  try {
    parsed = body ? JSON.parse(body) : null;
  } catch {
    parsed = null;
  }
  if (!res.ok) {
    throw new ApiError(parsed?.message || parsed?.detail || res.statusText, res.status);
  }
  return parsed as T;
}

const get = <T>(path: string) => request<T>(path);
const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: 'POST', body: JSON.stringify(body ?? {}) });

// ---------------------------------------------------------------- types

export type Verdict = 'SAFE' | 'MARGINAL' | 'DO_NOT_CROSS';

export interface HullComparisonRow {
  hull_class: string;
  hull_label: string;
  verdict: Verdict;
  index_value: number;
  index_marginal: number;
  index_unsafe: number;
  turn_back_label: string | null;
}

export interface HingeEvent {
  type: string;
  cause: string;
}

export interface TraceStep {
  agent: string;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  ms: number;
  hinge: HingeEvent | null;
}

export interface SourceRow {
  source_id: string;
  provider: string;
  country: string;
  variables: string[] | Record<string, unknown>;
  resolution_km: number;
  access_status: 'CONNECTED' | 'ATTEMPTED' | 'SUBSTITUTED';
  priority_tier: number;
  tier_label?: string;
  provenance: string;
  last_pull_ts: string | null;
}

export interface DiscoveryPerVariable {
  variable: string;
  candidates: { provider: string; priority_tier: number; access_status: string }[];
  chosen: string | null;
  priority_tier: number | null;
  attempted_first: string | null;
  failed: string[];
}

export interface QueryResponse {
  answer: string;
  verdict: Verdict;
  index_value: number;
  hull_class: string;
  hull_label: string;
  date: string;
  return_window: { start_label: string; end_label: string } | null;
  turn_back_time: string | null;
  trace_id: string;
  advisory_id: string;
  guard: { result: 'PASS' | 'REJECT'; reason: string };
  sources: SourceRow[];
  discovery_log: {
    candidates_considered: string[];
    chosen_source: string | null;
    priority_tier: number | null;
    reason: string;
    fallback_occurred: boolean;
    failed: string[];
    per_variable: DiscoveryPerVariable[];
  };
  layers: string[];
  language: string;
  intent: string;
  context: Record<string, any>;
  updated_fields: string[];
  hourly: {
    hour: number; index: number; verdict: Verdict; hs_m: number; tide_stage: string;
  }[];
  hull_comparison: HullComparisonRow[];
  official_advisory: { text_en: string; severity: string; issuer: string; provenance: string };
  disagreement: boolean;
  hinge_events: HingeEvent[];
  provenance: string;
  date_mapped_from_request: boolean;
  broadcast: BroadcastBundle;
  intent_result: IntentResult | null;
}

export interface IntentResult {
  kind: 'nearest_pfz' | 'geofence_check' | 'route_advisory' | 'productivity';
  answer: string;
  ground?: string;
  points?: { pfz_id: string; distance_km: number; bearing_deg: number; depth_m: number }[];
  zones?: { name: string; type: string; status: string; distance_km: number }[];
  breach_count?: number;
  distance_nm?: number; bearing_deg?: number; eta_hours?: number | null;
  status?: string;
}

export interface BroadcastBundle {
  sms: { content: string; char_count: number; limit: number; over_limit: boolean };
  vhf: { content: string; audio_url: string; audio_is_placeholder: boolean };
  slip: { content: string; page_size: string };
  board: {
    headline: string; inlet: string; date: string; footer: string;
    buckets: { hull_label: string; verdict: Verdict; short: string; index_value: number }[];
  };
  channels: {
    channel: string; owner: string; licence_required: string;
    unit_cost_inr: number; tier: number;
  }[];
  monthly_infra_inr_10_centres: number;
  notice: string;
}

export interface Health {
  pipeline_status: 'active' | 'stale' | 'halted' | 'failed';
  connected_sources: string[];
  primary_source: string | null;
  last_pull: string | null;
  staleness_hours: number;
  stale_warn_hours: number;
  stale_halt_hours: number;
  record: { start: string; years: number; provenance: string };
}

export interface Contingency {
  hits: number; misses: number; false_alarms: number; correct_negatives: number;
  pod: number; far: number; days_per_year: number; total_days: number; event_count: number;
}

export interface Validation {
  threshold: number;
  reference_hull: string;
  record: { start: string; end: string; days: number };
  contingency: Contingency;
  baseline: Contingency & { definition: string };
  skill: {
    beats_baseline: boolean;
    statement: string;
    criterion: string;
    equal_pod_point: (Contingency & { threshold: number }) | null;
    pod_delta: number;
    far_delta: number;
  };
  roc: { threshold: number; pod: number; far: number; days_per_year: number }[];
  incidents: {
    date: string; index_value: number; hs_m: number; verdict: string;
    flagged: boolean; source_url: string | null; provenance: string;
  }[];
  failure_case: {
    date: string; index_value: number; threshold: number; predicted_verdict: string;
    actual_outcome: string; diagnosis: string;
    conditions: { hs_m: number; tp_s: number; tide_stage: string; dir_deg: number };
  } | null;
  limits: string[];
  provenance: string;
}

export interface Persona {
  persona_id: string;
  label: string;
  default_layers: string[];
  answer_framing: string;
  suggested_queries: string[];
}

export interface Boat {
  boat_id: string; hull_class: string; length_m: number; engine_hp: number;
  crew: number; home_harbour: string; threshold_bucket: string;
}

export interface AlertRow {
  alert_id: string; boat_id: string;
  boat: { hull_class: string; length_m: number; home_harbour: string } | null;
  trigger_type: string; severity: 'severe' | 'warning' | 'advisory';
  source_id: string | null; verdict: Verdict | null; index_value: number | null;
  hull_class: string | null; state: 'PENDING_RELEASE' | 'RELEASED';
  released_by: string | null; released_at: string | null; created_at: string | null;
  trigger_detail: Record<string, any> | null;
}

// ---------------------------------------------------------------- endpoints

export const api = {
  health: () => get<Health>('/api/health'),

  query: (body: {
    session_id: string; query_text: string; persona?: string; force_failure?: boolean; stream?: boolean; user_lat?: number; user_lon?: number; gps_error?: string; boat_id?: string;
  }) => post<QueryResponse>('/api/query', body),

  queryStream: async function* (body: {
    session_id: string; query_text: string; persona?: string; force_failure?: boolean; stream?: boolean; user_lat?: number; user_lon?: number; gps_error?: string; boat_id?: string;
  }) {
    body.stream = true;
    const res = await fetch(API_URL + '/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!res.ok) {
      const bodyText = await res.text();
      let parsed = null;
      try { parsed = JSON.parse(bodyText); } catch {}
      throw new ApiError(parsed?.message || parsed?.detail || res.statusText, res.status);
    }
    const reader = res.body?.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (reader) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          yield JSON.parse(line.slice(6));
        }
      }
    }
  },

  trace: (traceId: string) =>
    get<{ trace_id: string; nodes: { steps: TraceStep[] }; hinge_events: { events: HingeEvent[] } }>(
      `/api/trace/${traceId}`),

  sources: () => get<{
    sources: SourceRow[];
    summary: Record<string, number>;
    rule: string;
  }>('/api/sources'),

  addSource: (body: Record<string, unknown>) => post('/api/registry', body),

  coverage: () => get<{
    rows: { id: number; requirement: string; note: string; status: 'BUILT' | 'MOCKUP' }[];
    summary: { built: number; mockup: number; total: number };
  }>('/api/coverage'),

  personas: () => get<{ personas: Persona[] }>('/api/personas'),

  officers: () => get<{
    officers: { officer_id: string; name: string; role: string }[];
    note: string;
  }>('/api/personas/officers'),

  validation: (threshold?: number) =>
    get<Validation>(`/api/validation${threshold != null ? `?threshold=${threshold}` : ''}`),

  boats: () => get<Boat[]>('/api/boats'),
  createBoat: (body: Boat) => post<Boat>('/api/boats', body),
  deleteBoat: (id: string) => request(`/api/boats/${id}`, { method: 'DELETE' }),

  alerts: () => get<{
    alerts: AlertRow[];
    summary: Record<string, number>;
    note: string;
  }>('/api/alerts'),
  releaseAlert: (id: string, officer_name: string) =>
    post<AlertRow>(`/api/alerts/${id}/release`, { officer_name }),
  alertBroadcast: (id: string) => get<BroadcastBundle>(`/api/alerts/${id}/broadcast`),

  sentinelTrigger: () => post<{
    boats_checked: number; alerts_created: number; duration_s: number;
  }>('/api/sentinel/trigger'),
  sentinelStatus: () => get<{
    running: boolean; active_jobs: number; interval_minutes: number; last_run: string | null;
  }>('/api/sentinel/status'),

  advisoryLatest: () => get<any>('/api/advisory/latest'),
  advisoryBroadcast: (id: string) => get<BroadcastBundle & { state: string }>(
    `/api/advisory/${id}/broadcast`),
  releaseAdvisory: (id: string, officer_name: string) =>
    post<any>(`/api/advisory/${id}/release`, { officer_name }),

  mapLayers: (verdict?: string, index?: number, lat?: number, lon?: number, boat_id?: string) => {
    let url = `/api/map/layers?`;
    const params = new URLSearchParams();
    if (verdict) params.set('verdict', verdict);
    if (index != null) params.set('index_value', index.toString());
    if (lat != null) params.set('user_lat', lat.toString());
    if (lon != null) params.set('user_lon', lon.toString());
    if (boat_id != null) params.set('boat_id', boat_id);
    return get<Record<string, any>>(url + params.toString());
  },

  grounds: () => get<{ grounds: { ground_id: string; local_name: string; radius_km: number }[];
    privacy_note: string; }>('/api/grounds'),
  route: (destGround: string, cruiseKnots = 7) =>
    post<{
      origin: { lat: number; lon: number; name: string };
      destination: { ground_id: string; local_name: string };
      bearing_deg: number; distance_km: number; distance_nm: number;
      eta_hours: number | null;
      waypoints: { lat: number; lon: number; distance_km: number }[];
      method: string; status: string; caveat: string;
    }>('/api/route', { dest_ground: destGround, cruise_knots: cruiseKnots }),

  geofence: (groundId: string) => get<any>(`/api/geofence/check?ground_id=${groundId}`),
  pfz: (groundId: string, limit = 5) =>
    get<any>(`/api/pfz/nearest?ground_id=${groundId}&limit=${limit}`),
  productivity: () => get<any>('/api/productivity'),
  degradationModes: () => get<{ modes: { id: string; label: string; rule: string; effect: string }[] }>(
    '/api/demo/degradation-modes'),
};
