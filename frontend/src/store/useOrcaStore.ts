import { create } from 'zustand';

export interface Boat {
  boatId: string;
  hullClass: string;
  lengthM: number;
  engineHp: number;
  homeHarbour: string;
  usualGrounds: string[];
}

export interface Advisory {
  advisoryId: string;
  verdict: 'SAFE' | 'MARGINAL' | 'DO_NOT_CROSS';
  indexValue: number;
}

export interface PipelineStatus {
  isFresh: boolean;
  stalenessHours: number;
  source: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  text: string;
  verdict?: 'SAFE' | 'MARGINAL' | 'DO_NOT_CROSS' | 'UNKNOWN';
  metrics?: {
    returnWindow?: string;
    turnBackTime?: string;
  };
}

interface OrcaState {
  sessionId: string | null;
  activeBoat: Boat | null;
  language: 'en' | 'ml' | 'ta';
  persona: 'fisherman' | 'disaster_mgmt' | 'coast_guard' | 'policy_maker' | 'researcher';
  activeTab: 'platform' | 'alerts' | 'validation' | 'coverage' | 'offline_compile' | 'trust';
  activeAdvisory: Advisory | null;
  pipelineStatus: PipelineStatus;
  unreleasedAlertsCount: number;
  officialAdvisoryText: string;
  officialAdvisoryVerdict: 'SAFE' | 'MARGINAL' | 'DO_NOT_CROSS' | null;
  guardDisagreement: boolean;
  isBoatModalOpen: boolean;
  
  // Chat State
  chatHistory: ChatMessage[];
  isQuerying: boolean;
  activeTrace: any; // Store the trace data for EvidencePane
  activeSources: any[]; // Store sources for EvidencePane

  // Actions
  setLanguage: (lang: 'en' | 'ml' | 'ta') => void;
  setActiveTab: (tab: OrcaState['activeTab']) => void;
  setBoatModalOpen: (isOpen: boolean) => void;
  setActiveBoat: (boat: Boat) => void;
  submitQuery: (text: string) => Promise<void>;
}

export const useOrcaStore = create<OrcaState>((set, get) => ({
  sessionId: crypto.randomUUID(), // Initialize with a real UUID
  activeBoat: null,
  language: 'en',
  persona: 'fisherman',
  activeTab: 'platform',
  activeAdvisory: null,
  pipelineStatus: { isFresh: true, stalenessHours: 0, source: 'MOSDAC' },
  unreleasedAlertsCount: 0,
  officialAdvisoryText: 'INCOIS: Generally safe for all operations.',
  officialAdvisoryVerdict: 'SAFE',
  guardDisagreement: false,
  isBoatModalOpen: false,
  
  chatHistory: [],
  isQuerying: false,
  activeTrace: null,
  activeSources: [],
  
  setLanguage: (lang) => set({ language: lang }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setBoatModalOpen: (isOpen) => set({ isBoatModalOpen: isOpen }),
  setActiveBoat: (boat) => set({ activeBoat: boat }),
  
  submitQuery: async (text: string) => {
    const { sessionId, chatHistory } = get();
    
    // Optimistic UI update
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: 'user', text };
    set({ chatHistory: [...chatHistory, userMsg], isQuerying: true });

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          query_text: text
        })
      });

      if (!response.ok) throw new Error('API Error');
      const data = await response.json();

      const agentMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'agent',
        text: data.answer,
        verdict: data.verdict,
        metrics: {
          returnWindow: data.return_window?.window || 'N/A'
        }
      };

      set((state) => ({
        chatHistory: [...state.chatHistory, agentMsg],
        isQuerying: false,
        activeSources: data.sources || [],
        // In a real app we'd fetch the full trace by ID, but we'll store basic metadata here
        activeTrace: { id: data.trace_id, guard: data.guard }
      }));
    } catch (error) {
      console.error("Failed to fetch query:", error);
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'agent',
        text: "System error: Failed to reach the ORCA engine. Please check your connection.",
        verdict: 'UNKNOWN'
      };
      set((state) => ({ chatHistory: [...state.chatHistory, errorMsg], isQuerying: false }));
    }
  }
}));
