import React, { useState } from 'react';
import { AlertTriangle, Radio, CheckCircle, Info, ChevronDown } from 'lucide-react';

export default function AlertsTab() {
  const [filter, setFilter] = useState<'All' | 'Advisory' | 'Warning' | 'Severe'>('All');
  
  const alerts = [
    { id: 'ALT-1092', severity: 'Severe', title: 'DO_NOT_CROSS: 4.5m Swell Approaching', time: '10 mins ago', hull: 'FRP Skiff, Plywood Canoe' },
    { id: 'ALT-1091', severity: 'Warning', title: 'MARGINAL: Ebb Tide Peak at 14:00', time: '1 hr ago', hull: 'FRP Skiff' },
    { id: 'ALT-1090', severity: 'Advisory', title: 'SAFE: Conditions clearing post-squall', time: '4 hrs ago', hull: 'All Classes' },
  ];

  const filtered = filter === 'All' ? alerts : alerts.filter(a => a.severity === filter);

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-slate-800">Sentinel Proactive Alerts</h2>
        <div className="flex space-x-2 bg-gray-100 p-1 rounded-lg">
          {['All', 'Advisory', 'Warning', 'Severe'].map(f => (
            <button 
              key={f} 
              onClick={() => setFilter(f as any)}
              className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${filter === f ? 'bg-white shadow text-blue-600' : 'text-gray-600 hover:bg-gray-200'}`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        {filtered.map(alert => (
          <div key={alert.id} className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden flex flex-col">
            <div className="p-5 flex justify-between items-start">
              <div className="flex items-start space-x-4">
                <div className={`p-3 rounded-full mt-1 ${
                  alert.severity === 'Severe' ? 'bg-red-100 text-red-600' : 
                  alert.severity === 'Warning' ? 'bg-amber-100 text-amber-600' : 'bg-blue-100 text-blue-600'
                }`}>
                  {alert.severity === 'Severe' && <AlertTriangle className="w-6 h-6" />}
                  {alert.severity === 'Warning' && <Info className="w-6 h-6" />}
                  {alert.severity === 'Advisory' && <CheckCircle className="w-6 h-6" />}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-800">{alert.title}</h3>
                  <div className="flex items-center space-x-3 text-sm text-gray-500 mt-1">
                    <span className="font-mono bg-gray-100 px-2 py-0.5 rounded text-xs">{alert.id}</span>
                    <span>{alert.time}</span>
                    <span>•</span>
                    <span className="font-medium text-slate-600">Affected: {alert.hull}</span>
                  </div>
                </div>
              </div>
              <button className="bg-blue-50 text-blue-600 px-4 py-2 rounded-lg font-bold text-sm hover:bg-blue-100 transition-colors flex items-center">
                <Radio className="w-4 h-4 mr-2" /> Broadcast / Release
              </button>
            </div>
            {/* Expanded Content Mock */}
            {alert.severity === 'Severe' && (
              <div className="bg-slate-50 border-t p-4 text-sm text-gray-700 flex flex-col gap-2">
                <p><strong>Trigger Detail:</strong> Deterministic hazard index breached unsafe threshold (0.75 > 0.70) primarily driven by offshore swell height (4.5m) and aligning channel bearing.</p>
                <p><strong>Action Required:</strong> Immediate broadcast to VHF channel 16 and SMS push to all registered FRP owners.</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
