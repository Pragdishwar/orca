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
  
  // Actions
  setLanguage: (lang: 'en' | 'ml' | 'ta') => void;
  setActiveTab: (tab: OrcaState['activeTab']) => void;
  setBoatModalOpen: (isOpen: boolean) => void;
  setActiveBoat: (boat: Boat) => void;
}

export const useOrcaStore = create<OrcaState>((set) => ({
  sessionId: null,
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
  
  setLanguage: (lang) => set({ language: lang }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setBoatModalOpen: (isOpen) => set({ isBoatModalOpen: isOpen }),
  setActiveBoat: (boat) => set({ activeBoat: boat }),
}));
