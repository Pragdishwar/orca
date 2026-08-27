import React from 'react';
import { Target, Activity, CheckCircle, XCircle } from 'lucide-react';

export default function ValidationTab() {
  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Contingency Matrix */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 md:col-span-1">
          <h3 className="font-bold text-gray-800 mb-4">2x2 Contingency Matrix</h3>
          <div className="grid grid-cols-2 gap-2 text-center text-sm font-medium">
            <div className="bg-emerald-100 text-emerald-800 p-4 rounded-lg flex flex-col justify-center">
              <span className="text-2xl font-black mb-1">45</span>
              <span>Hits (Correct Warn)</span>
            </div>
            <div className="bg-red-100 text-red-800 p-4 rounded-lg flex flex-col justify-center">
              <span className="text-2xl font-black mb-1">12</span>
              <span>False Alarms</span>
            </div>
            <div className="bg-amber-100 text-amber-800 p-4 rounded-lg flex flex-col justify-center">
              <span className="text-2xl font-black mb-1">2</span>
              <span>Misses (Fail to Warn)</span>
            </div>
            <div className="bg-gray-100 text-gray-800 p-4 rounded-lg flex flex-col justify-center">
              <span className="text-2xl font-black mb-1">200</span>
              <span>Correct Negatives</span>
            </div>
          </div>
        </div>

        {/* Metric Tiles */}
        <div className="md:col-span-2 grid grid-cols-2 gap-4">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex flex-col justify-center items-center text-center">
            <Target className="w-8 h-8 text-blue-500 mb-2" />
            <h4 className="text-gray-500 font-bold uppercase text-xs mb-1">Probability of Detection (POD)</h4>
            <span className="text-4xl font-black text-slate-800">95.7%</span>
            <span className="text-xs text-emerald-500 font-bold mt-2">↑ 12% vs Baseline</span>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex flex-col justify-center items-center text-center">
            <Activity className="w-8 h-8 text-amber-500 mb-2" />
            <h4 className="text-gray-500 font-bold uppercase text-xs mb-1">False Alarm Ratio (FAR)</h4>
            <span className="text-4xl font-black text-slate-800">21.0%</span>
            <span className="text-xs text-emerald-500 font-bold mt-2">↓ 5% vs Baseline</span>
          </div>
        </div>
      </div>

      {/* Benchmark Comparison */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <h3 className="font-bold text-gray-800 mb-4">Benchmark Comparison: ORCA vs Naive Baseline (Hs &gt; 2.0m)</h3>
        <table className="w-full text-sm text-left">
          <thead className="bg-gray-50 text-gray-600 font-bold">
            <tr>
              <th className="p-3 rounded-tl-lg">Model</th>
              <th className="p-3">POD</th>
              <th className="p-3">FAR</th>
              <th className="p-3 rounded-tr-lg">Days Flagged / Yr</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b">
              <td className="p-3 font-medium text-gray-800">Naive Baseline</td>
              <td className="p-3">83.5%</td>
              <td className="p-3">26.0%</td>
              <td className="p-3">85 days</td>
            </tr>
            <tr className="bg-blue-50/50">
              <td className="p-3 font-bold text-blue-800 flex items-center">ORCA Engine</td>
              <td className="p-3 font-bold text-emerald-600">95.7%</td>
              <td className="p-3 font-bold text-emerald-600">21.0%</td>
              <td className="p-3 font-bold text-blue-700">62 days (Optimized)</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Detailed Failure Case & Incidents */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h3 className="font-bold text-red-800 flex items-center mb-4"><XCircle className="w-5 h-5 mr-2" /> Detailed Failure Case Analysis</h3>
          <div className="space-y-2 text-sm text-gray-700">
            <p><strong className="text-gray-900">Date:</strong> 2023-07-10 (Monsoon Squall)</p>
            <p><strong className="text-gray-900">Predicted Verdict:</strong> SAFE (Index 0.38)</p>
            <p><strong className="text-gray-900">Actual Outcome:</strong> Boat Capsized at Inlet</p>
            <div className="mt-4 bg-red-50 p-3 rounded border border-red-100 text-red-900">
              <strong>Root-Cause Diagnosis:</strong> Sudden localized wind burst generated short-period chop (Tp = 4s) inside the channel. Our 0.25° wave grid resolved conditions 15km offshore, entirely missing the localized topographical funneling effect.
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h3 className="font-bold text-gray-800 mb-4">Historical Incidents (Test Set)</h3>
          <ul className="space-y-3 text-sm">
            <li className="flex justify-between items-center border-b pb-2">
              <span className="font-medium text-gray-800">2023-07-10 Capsize</span>
              <a href="#" className="text-blue-600 hover:underline">Read Report</a>
            </li>
            <li className="flex justify-between items-center border-b pb-2">
              <span className="font-medium text-gray-800">2022-09-15 Engine Failure (Grounding)</span>
              <a href="#" className="text-blue-600 hover:underline">Read Report</a>
            </li>
            <li className="flex justify-between items-center pb-2">
              <span className="font-medium text-gray-800">2021-08-02 Wave Overtopping</span>
              <a href="#" className="text-blue-600 hover:underline">Read Report</a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
