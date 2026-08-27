import React, { useState } from 'react';
import { Network, Server, ShieldAlert, CheckCircle2, AlertTriangle, ArrowRight } from 'lucide-react';

export default function EvidencePane() {
  const [activeTab, setActiveTab] = useState<'trace' | 'sources' | 'limits'>('trace');

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Sub-tabs Header */}
      <div className="flex border-b bg-gray-50">
        <button 
          onClick={() => setActiveTab('trace')}
          className={`flex-1 py-3 text-xs font-bold uppercase tracking-wider ${activeTab === 'trace' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
        >
          <Network className="w-4 h-4 mx-auto mb-1" /> Trace DAG
        </button>
        <button 
          onClick={() => setActiveTab('sources')}
          className={`flex-1 py-3 text-xs font-bold uppercase tracking-wider ${activeTab === 'sources' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
        >
          <Server className="w-4 h-4 mx-auto mb-1" /> Sources
        </button>
        <button 
          onClick={() => setActiveTab('limits')}
          className={`flex-1 py-3 text-xs font-bold uppercase tracking-wider ${activeTab === 'limits' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
        >
          <ShieldAlert className="w-4 h-4 mx-auto mb-1" /> Limits
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'trace' && (
          <div className="space-y-6">
            <h3 className="text-sm font-bold text-gray-800 mb-4">Execution Trace</h3>
            
            <div className="relative border-l-2 border-gray-200 ml-3 space-y-6">
              
              <div className="relative pl-6">
                <span className="absolute -left-2.5 top-0.5 bg-white border-2 border-emerald-500 rounded-full w-4 h-4"></span>
                <h4 className="text-sm font-bold text-gray-700">Planner Node</h4>
                <p className="text-xs text-gray-500 mt-1">Intent: Safety Check. Extracted Slots: Location(Muthalapozhi), Time(Tomorrow).</p>
              </div>

              <div className="relative pl-6">
                <span className="absolute -left-2.5 top-0.5 bg-white border-2 border-emerald-500 rounded-full w-4 h-4"></span>
                <h4 className="text-sm font-bold text-gray-700">Discovery Node</h4>
                <p className="text-xs text-gray-500 mt-1">Resolved physics requirements. Selected Tier-1 fallback (MOSDAC).</p>
              </div>

              {/* Hinge Event */}
              <div className="relative pl-6">
                <span className="absolute -left-2.5 top-0.5 bg-amber-500 shadow-[0_0_0_4px_rgba(245,158,11,0.2)] rounded-full w-4 h-4 animate-pulse"></span>
                <div className="border border-amber-300 bg-amber-50 p-3 rounded-lg shadow-sm">
                  <div className="flex items-center text-amber-800 font-bold text-sm mb-1">
                    <AlertTriangle className="w-4 h-4 mr-1" /> HINGE EVENT: Risk Node
                  </div>
                  <p className="text-xs text-amber-900 leading-relaxed">
                    Hazard Engine evaluation shifted baseline verdict from <strong className="bg-emerald-200 px-1 rounded text-emerald-900">SAFE</strong> <ArrowRight className="inline w-3 h-3" /> <strong className="bg-red-200 px-1 rounded text-red-900">DO_NOT_CROSS</strong>.
                    <br/><br/>
                    <strong>Cause:</strong> Ebb tide penalty (rate=2.0) compounded with wave height (4.0m) exceeding FRP Skiff breaking limits.
                  </p>
                </div>
              </div>

              <div className="relative pl-6">
                <span className="absolute -left-2.5 top-0.5 bg-white border-2 border-emerald-500 rounded-full w-4 h-4"></span>
                <h4 className="text-sm font-bold text-gray-700">Synthesis Node</h4>
                <p className="text-xs text-gray-500 mt-1">Generated localized warning payload complying with Sovereign numbering rule.</p>
              </div>

              <div className="relative pl-6">
                <span className="absolute -left-2.5 top-0.5 bg-emerald-500 rounded-full w-4 h-4 flex items-center justify-center">
                  <CheckCircle2 className="w-3 h-3 text-white" />
                </span>
                <h4 className="text-sm font-bold text-emerald-700">Guard Node</h4>
                <p className="text-xs text-emerald-600 mt-1">Deterministic check passed. No contradictions found.</p>
              </div>

            </div>
          </div>
        )}

        {activeTab === 'sources' && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-gray-800 mb-2">Dataset Provenance</h3>
            
            <div className="border border-gray-200 rounded-lg p-3">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="text-sm font-bold">MOSDAC (ISRO)</h4>
                  <span className="text-[10px] text-gray-500 font-mono">TIER 1 (INDIAN)</span>
                </div>
                <span className="bg-emerald-100 text-emerald-700 border border-emerald-200 text-xs px-2 py-0.5 rounded font-bold">LIVE</span>
              </div>
              <div className="text-xs text-gray-600 space-y-1">
                <p><span className="font-semibold text-gray-400">VARS:</span> Wave Hs, Dir, Tp</p>
                <p><span className="font-semibold text-gray-400">TYPE:</span> <span className="bg-blue-50 text-blue-600 px-1 rounded">REAL-TIME</span></p>
                <p><span className="font-semibold text-gray-400">AGE:</span> 2 hours</p>
              </div>
            </div>

            <div className="border border-gray-200 rounded-lg p-3 opacity-60">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="text-sm font-bold text-gray-500">Copernicus Marine</h4>
                  <span className="text-[10px] text-gray-400 font-mono">TIER 2 (FOREIGN)</span>
                </div>
                <span className="bg-gray-100 text-gray-500 border border-gray-200 text-xs px-2 py-0.5 rounded font-bold">SUBSTITUTED</span>
              </div>
              <div className="text-xs text-gray-500 space-y-1">
                <p>Not utilized due to Sovereign Priority (Rule R-8). Tier 1 successfully resolved all required physics variables.</p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'limits' && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-gray-800 mb-2">System Limitations</h3>
            <div className="bg-blue-50 border border-blue-200 text-blue-800 p-3 rounded-lg text-sm space-y-3">
              <p><strong>Scope of Calibration:</strong> Physics models are strictly calibrated to the geometry of Muthalapozhi Inlet (8.636° N, 76.786° E).</p>
              <p><strong>Absence of High-Res Bathymetry:</strong> Calculations assume a uniform channel depth profile. Localized sandbar shifts are NOT modeled dynamically.</p>
              <p><strong>Shallow-Water Breaking Limits:</strong> Near-shore breaking calculations for FRP Skiffs are derived from hindcast regressions and contain a ±15% margin of error during South-West Monsoon squalls.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
