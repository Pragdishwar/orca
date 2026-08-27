import React, { useState } from 'react';
import { SlidersHorizontal, ShieldCheck, UserCheck, AlertOctagon } from 'lucide-react';
import { useOrcaStore } from '../store/useOrcaStore';

export default function TrustTab() {
  const [threshold, setThreshold] = useState(0.5);
  const [officerName, setOfficerName] = useState('');
  
  // Zustand state to demo forced failure
  const { guardDisagreement } = useOrcaStore();
  
  const handleForceFailure = () => {
    useOrcaStore.setState({ guardDisagreement: true });
    alert("Forced LLM Contradiction! Guard will intercept and switch Advisory Strip to AMBER.");
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      
      {/* Calibration Controls */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="font-bold text-gray-800 flex items-center mb-6">
          <SlidersHorizontal className="w-5 h-5 mr-2 text-blue-600" /> Community Threshold Calibration
        </h3>
        
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">Hazard Index Alerting Threshold</span>
            <span className="bg-blue-100 text-blue-800 font-bold px-3 py-1 rounded-full">{threshold.toFixed(2)}</span>
          </div>
          <input 
            type="range" min="0" max="1" step="0.05" 
            value={threshold} 
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600" 
          />
          <div className="flex justify-between text-xs text-gray-400 mt-2 font-medium uppercase">
            <span>Risk Tolerant (Higher Misses)</span>
            <span>Balanced</span>
            <span>Risk Averse (Higher False Alarms)</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg border text-center">
            <div className="text-sm text-gray-500 font-bold uppercase mb-1">Simulated POD</div>
            <div className="text-2xl font-black text-emerald-600">{Math.min(99.9, 95.7 + (0.5 - threshold) * 20).toFixed(1)}%</div>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg border text-center">
            <div className="text-sm text-gray-500 font-bold uppercase mb-1">Simulated FAR</div>
            <div className="text-2xl font-black text-amber-600">{Math.max(5.0, 21.0 - (0.5 - threshold) * 15).toFixed(1)}%</div>
          </div>
        </div>
      </div>

      {/* Human-in-the-loop Release */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="font-bold text-gray-800 flex items-center mb-6">
          <UserCheck className="w-5 h-5 mr-2 text-blue-600" /> Human-in-the-Loop Release Panel
        </h3>
        <div className="flex items-end space-x-4">
          <div className="flex-1">
            <label className="block text-sm font-semibold text-gray-600 mb-1">Authorizing Officer Name / ID</label>
            <input 
              type="text" 
              value={officerName}
              onChange={(e) => setOfficerName(e.target.value)}
              placeholder="e.g. Cmdr. Rajesh"
              className="w-full border rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button 
            disabled={!officerName}
            className="bg-blue-600 text-white font-bold px-6 py-2 rounded-lg shadow hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors h-[42px]"
          >
            Authorize & Release Advisory
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Privacy Audit */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="font-bold text-gray-800 flex items-center mb-4">
            <ShieldCheck className="w-5 h-5 mr-2 text-emerald-600" /> Privacy Guard Audit
          </h3>
          <p className="text-sm text-gray-600 leading-relaxed mb-4">
            ORCA strictly adheres to the data minimization mandate. Raw GPS traces are mathematically purged upon safe return.
          </p>
          <ul className="text-sm space-y-2 text-gray-700 font-medium">
            <li className="flex items-center"><CheckCircle className="w-4 h-4 text-emerald-500 mr-2"/> Named grounds storage only (e.g., "Quilon Bank")</li>
            <li className="flex items-center"><CheckCircle className="w-4 h-4 text-emerald-500 mr-2"/> No continuous coordinate logging</li>
            <li className="flex items-center"><CheckCircle className="w-4 h-4 text-emerald-500 mr-2"/> Offline local caching authorized</li>
          </ul>
        </div>

        {/* Guard Demo */}
        <div className="bg-red-50 rounded-xl shadow-sm border border-red-200 p-6 flex flex-col justify-center items-center text-center">
          <h3 className="font-bold text-red-800 flex items-center mb-2">
            <AlertOctagon className="w-5 h-5 mr-2" /> Deterministic Guard Demo
          </h3>
          <p className="text-sm text-red-700 mb-4">
            Simulate a catastrophic LLM hallucination (Rule R-1 violation) to trigger immediate fallback to INCOIS advisory.
          </p>
          <button 
            onClick={handleForceFailure}
            className="bg-red-600 text-white font-bold px-4 py-2 rounded-lg shadow hover:bg-red-700 transition-colors"
          >
            Force Guard Rejection
          </button>
        </div>
      </div>
      
    </div>
  );
}

// Quick inline icon component to avoid missing import errors for CheckCircle if not in lucide
const CheckCircle = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>
);
