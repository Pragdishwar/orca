import React from 'react';
import { CheckCircle2, FlaskConical } from 'lucide-react';

export default function CoverageTab() {
  const requirements = [
    { id: '1', title: 'Deterministic Hazard Calculation (Physics-based)', status: 'BUILT' },
    { id: '2', title: 'Sovereign Dataset Priority (Rule R-8)', status: 'BUILT' },
    { id: '3', title: 'LLM Synthesized Multilingual Advisories', status: 'BUILT' },
    { id: '4', title: 'Deterministic Safety Guard (Rule R-1)', status: 'BUILT' },
    { id: '5', title: 'Proactive Sentinel Background Task', status: 'BUILT' },
    { id: '6', title: 'Staleness Decay Fallback (Rule R-2)', status: 'BUILT' },
    { id: '7', title: 'H3-based Optimal Route Corridors', status: 'MOCKUP' },
    { id: '8', title: 'Geofence Checks (IMBL / MPA)', status: 'MOCKUP' },
    { id: '9', title: 'Boat Profile Registration & Thresholds', status: 'BUILT' },
    { id: '10', title: 'Broadcast Compilation (4-Tier)', status: 'MOCKUP' },
    { id: '11', title: 'Interactive Calibration Controls (Trust)', status: 'BUILT' },
    { id: '12', title: 'Privacy Audit (Named Grounds Only)', status: 'BUILT' },
    { id: '13', title: 'Trace & DAG Visualizer', status: 'BUILT' },
    { id: '14', title: 'Live Metric Validation Matrix', status: 'BUILT' },
  ];

  const builtCount = requirements.filter(r => r.status === 'BUILT').length;
  const mockupCount = requirements.length - builtCount;

  return (
    <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="bg-slate-900 p-6 text-white flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Requirement Coverage Matrix</h2>
          <p className="text-slate-400 text-sm mt-1">14-Row Problem Statement Alignment</p>
        </div>
        <div className="bg-slate-800 border border-slate-700 px-4 py-2 rounded-lg text-sm font-bold flex space-x-3">
          <span className="text-emerald-400">{builtCount} BUILT</span>
          <span className="text-slate-500">·</span>
          <span className="text-blue-400">{mockupCount} MOCKUP</span>
        </div>
      </div>
      
      <table className="w-full text-left text-sm">
        <thead className="bg-gray-50 border-b">
          <tr>
            <th className="px-6 py-4 font-bold text-gray-600">ID</th>
            <th className="px-6 py-4 font-bold text-gray-600">Feature Requirement</th>
            <th className="px-6 py-4 font-bold text-gray-600 text-right">Status</th>
          </tr>
        </thead>
        <tbody>
          {requirements.map((req, i) => (
            <tr key={req.id} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-6 py-4 font-mono text-gray-500">REQ-{req.id.padStart(2, '0')}</td>
              <td className="px-6 py-4 font-medium text-gray-800">{req.title}</td>
              <td className="px-6 py-4 text-right">
                {req.status === 'BUILT' ? (
                  <span className="inline-flex items-center bg-emerald-100 text-emerald-800 px-2.5 py-1 rounded-full text-xs font-bold">
                    <CheckCircle2 className="w-3 h-3 mr-1" /> BUILT
                  </span>
                ) : (
                  <span className="inline-flex items-center bg-blue-100 text-blue-800 px-2.5 py-1 rounded-full text-xs font-bold">
                    <FlaskConical className="w-3 h-3 mr-1" /> MOCKUP
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
