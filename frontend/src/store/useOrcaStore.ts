import { create } from 'zustand';
import {
  api, ApiError, AlertRow, Boat, Health, HingeEvent, Persona, QueryResponse,
  SourceRow, TraceStep, Verdict,
} from '../api/client';

export type TabId =
  | 'platform' | 'alerts' | 'validation' | 'offline_compile' | 'trust';

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  text: string;
  error?: boolean;
  response?: QueryResponse;
}

interface OrcaState {
  sessionId: string;
  activeTab: TabId;
  language: string;
  persona: string;
  personas: Persona[];

  boats: Boat[];
  activeBoat: Boat | null;
  isBoatModalOpen: boolean;

  health: Health | null;
  healthError: string | null;

  chatHistory: ChatMessage[];
  isQuerying: boolean;
  useMockChat: boolean;
  /** The most recent successful answer. Drives map, evidence and compile tabs. */
  active: QueryResponse | null;
  context: Record<string, any>;
  updatedFields: string[];

  trace: TraceStep[];
  hinges: HingeEvent[];
  sources: SourceRow[];
  sourcesRule: string;

  alerts: AlertRow[];
  alertSummary: Record<string, number>;

  bootError: string | null;

  setActiveTab: (t: TabId) => void;
  setPersona: (p: string) => void;
  setLanguage: (l: string) => void;
  setIsBoatModalOpen: (o: boolean) => void;
  setActiveBoat: (b: Boat | null) => void;
  setUseMockChat: (m: boolean) => void;

  boot: () => Promise<void>;
  refreshHealth: () => Promise<void>;
  refreshBoats: () => Promise<void>;
  refreshAlerts: () => Promise<void>;
  submitQuery: (text: string, opts?: { forceFailure?: boolean }) => Promise<void>;
  clearContextField: (field: string) => void;
}

const errText = (e: unknown) =>
  e instanceof ApiError ? e.message : e instanceof Error ? e.message : 'Unknown error';

export const useOrcaStore = create<OrcaState>((set, get) => ({
  sessionId: crypto.randomUUID(),
  activeTab: 'platform',
  language: 'en',
  persona: 'fisherman',
  personas: [],

  boats: [],
  activeBoat: null,
  isBoatModalOpen: false,

  health: null,
  healthError: null,

  chatHistory: [],
  isQuerying: false,
  useMockChat: false,
  active: null,
  context: {},
  updatedFields: [],

  trace: [],
  hinges: [],
  sources: [],
  sourcesRule: '',

  alerts: [],
  alertSummary: {},

  bootError: null,

  setActiveTab: (activeTab) => set({ activeTab }),
  setPersona: (persona) => set({ persona }),
  setLanguage: (language) => set({ language }),
  setIsBoatModalOpen: (isBoatModalOpen) => set({ isBoatModalOpen }),
  setActiveBoat: (activeBoat) => set({ activeBoat }),
  setUseMockChat: (useMockChat) => set({ useMockChat }),

  boot: async () => {
    try {
      const [health, personasRes, boats, sourcesRes, alertsRes] = await Promise.all([
        api.health(), api.personas(), api.boats(), api.sources(), api.alerts(),
      ]);
      set({
        health,
        healthError: null,
        personas: personasRes.personas,
        boats,
        activeBoat: get().activeBoat ?? boats[0] ?? null,
        sources: sourcesRes.sources,
        sourcesRule: sourcesRes.rule,
        alerts: alertsRes.alerts,
        alertSummary: alertsRes.summary,
        bootError: null,
      });
    } catch (e) {
      set({ bootError: errText(e), healthError: errText(e) });
    }
  },

  refreshHealth: async () => {
    try {
      set({ health: await api.health(), healthError: null });
    } catch (e) {
      set({ healthError: errText(e) });
    }
  },

  refreshBoats: async () => {
    try {
      const boats = await api.boats();
      const active = get().activeBoat;
      set({
        boats,
        activeBoat: active && boats.find((b) => b.boat_id === active.boat_id)
          ? active
          : boats[0] ?? null,
      });
    } catch { /* the panel shows its own error state */ }
  },

  refreshAlerts: async () => {
    try {
      const res = await api.alerts();
      set({ alerts: res.alerts, alertSummary: res.summary });
    } catch { /* handled in the tab */ }
  },

  clearContextField: (field) =>
    set((s) => ({ context: { ...s.context, [field]: '' } })),

  submitQuery: async (text, opts) => {
    const { sessionId, persona, chatHistory, activeBoat } = get();
    const trimmed = text.trim();
    if (!trimmed) return;

    // If a boat is selected and the utterance names no hull, steer the query
    // at that boat so the answer matches the boat in the header.
    const withBoat =
      activeBoat && !/canoe|trawler|frp|skiff|\d+\s*m\b/i.test(trimmed)
        ? `${trimmed} (${activeBoat.hull_class.replace(/_/g, ' ').toLowerCase()})`
        : trimmed;

    set({
      chatHistory: [...chatHistory,
        { id: crypto.randomUUID(), role: 'user', text: trimmed }],
      isQuerying: true,
    });

    try {
      const messageId = crypto.randomUUID();
      if (!get().useMockChat) {
        const stream = api.queryStream({
          session_id: sessionId,
          query_text: withBoat,
          persona,
          force_failure: opts?.forceFailure ?? false,
        });

        set((s) => ({
          chatHistory: [...s.chatHistory, { id: messageId, role: 'agent', text: '' }]
        }));

        let payload: QueryResponse | null = null;
        for await (const chunk of stream) {
          if (chunk.type === 'chunk') {
            set((s) => ({
              chatHistory: s.chatHistory.map((m) =>
                m.id === messageId ? { ...m, text: m.text + chunk.text } : m)
            }));
          } else if (chunk.type === 'done') {
            payload = chunk.payload;
          }
        }

        if (payload) {
          let trace: TraceStep[] = [];
          try {
            trace = (await api.trace(payload.trace_id)).nodes.steps;
          } catch { trace = []; }

          set((s) => ({
            chatHistory: s.chatHistory.map((m) =>
              m.id === messageId ? { ...m, response: payload } : m),
            isQuerying: false,
            active: payload,
            context: payload!.context,
            updatedFields: payload!.updated_fields,
            language: payload!.language,
            trace,
            hinges: payload!.hinge_events,
            sources: payload!.sources.length ? payload!.sources : s.sources,
          }));
          get().refreshHealth();
        }
      } else {
        const res = await api.query({
          session_id: sessionId,
          query_text: withBoat,
          persona,
          force_failure: opts?.forceFailure ?? false,
        });

        let trace: TraceStep[] = [];
        try {
          trace = (await api.trace(res.trace_id)).nodes.steps;
        } catch { trace = []; }

        set((s) => ({
          chatHistory: [...s.chatHistory,
            { id: messageId, role: 'agent', text: res.answer, response: res }],
          isQuerying: false,
          active: res,
          context: res.context,
          updatedFields: res.updated_fields,
          language: res.language,
          trace,
          hinges: res.hinge_events,
          sources: res.sources.length ? res.sources : s.sources,
        }));
        get().refreshHealth();
      }
    } catch (e) {
      set((s) => ({
        chatHistory: [...s.chatHistory, {
          id: crypto.randomUUID(), role: 'agent', error: true,
          text: `Could not reach the ORCA engine: ${errText(e)}`,
        }],
        isQuerying: false,
      }));
    }
  },
}));

export type { Verdict };
