import React from 'react';
import { Smartphone, Mic, Printer, Monitor, Copy, Play } from 'lucide-react';

export default function OfflineCompileTab() {
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-slate-800">4-Tier Broadcast Preview</h2>
        <div className="bg-white px-4 py-2 rounded-lg shadow-sm border border-gray-200 text-sm font-medium flex items-center space-x-4">
          <span className="text-gray-500">Channel Cost Breakdown:</span>
          <span className="text-emerald-600">SMS: ₹0.15/msg</span>
          <span className="text-blue-600">VHF: Free</span>
          <span className="text-purple-600">Print: ₹1.20/slip</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* SMS Preview */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col">
          <div className="bg-gray-50 p-3 border-b flex items-center justify-between">
            <h3 className="font-bold flex items-center text-gray-700"><Smartphone className="w-4 h-4 mr-2" /> SMS Text Push</h3>
            <span className="text-xs font-mono text-gray-500">114 / 160 CHARS</span>
          </div>
          <div className="p-6 flex-1 bg-gray-100 flex items-center justify-center">
            <div className="bg-green-100 border border-green-200 text-green-900 p-4 rounded-xl max-w-sm w-full relative shadow-sm">
              <p className="font-medium text-sm leading-relaxed">
                ORCA ADVISORY: DO NOT CROSS Muthalapozhi. 4.0m swell at 14:00 peak ebb tide. Extreme danger for small boats.
              </p>
              <button className="absolute -bottom-3 -right-3 bg-white p-2 rounded-full shadow hover:bg-gray-50">
                <Copy className="w-4 h-4 text-gray-600" />
              </button>
            </div>
          </div>
        </div>

        {/* VHF Audio */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col">
          <div className="bg-gray-50 p-3 border-b flex items-center justify-between">
            <h3 className="font-bold flex items-center text-gray-700"><Mic className="w-4 h-4 mr-2" /> VHF Radio Bulletin (Local)</h3>
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-bold">MALAYALAM</span>
          </div>
          <div className="p-6 flex-1 flex flex-col items-center justify-center space-y-4">
            <div className="w-full flex items-center space-x-4">
              <button className="bg-blue-600 text-white p-3 rounded-full hover:bg-blue-700">
                <Play className="w-5 h-5 ml-1" />
              </button>
              <div className="flex-1 flex space-x-1 h-8 items-center">
                {/* Dummy Audio Waveform */}
                {[...Array(20)].map((_, i) => (
                  <div key={i} className="flex-1 bg-blue-200 rounded-full" style={{ height: `${Math.max(20, Math.random() * 100)}%` }}></div>
                ))}
              </div>
            </div>
            <p className="text-sm text-gray-500 italic text-center w-full">
              "ഇന്ന് ഉച്ചയ്ക്ക് 2 മണിക്ക് മുതലപ്പൊഴിയിൽ ശക്തമായ തിരമാലകൾ..." 
            </p>
          </div>
        </div>

        {/* Printed A5 Slip */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col">
          <div className="bg-gray-50 p-3 border-b flex items-center justify-between">
            <h3 className="font-bold flex items-center text-gray-700"><Printer className="w-4 h-4 mr-2" /> Printable Slip (A5)</h3>
            <button className="text-xs font-bold text-blue-600 hover:underline">PRINT</button>
          </div>
          <div className="p-6 flex-1 flex items-center justify-center bg-gray-200">
            <div className="bg-white w-[250px] border-2 border-dashed border-gray-400 p-4 font-mono text-xs text-center shadow-lg transform rotate-1">
              <h4 className="font-black text-lg mb-1 border-b-2 border-black pb-2">ORCA WARNING</h4>
              <p className="py-2 font-bold text-lg">NO EXIT</p>
              <p className="pb-2 border-b-2 border-black">MUTHALAPOZHI INLET</p>
              <div className="text-left py-2 space-y-1">
                <p>TIME: 14:00 - 18:00</p>
                <p>WAVE: 4.0m SWELL</p>
                <p>TIDE: PEAK EBB</p>
              </div>
              <p className="text-[10px] mt-4">Auth: INCOIS / ORCA PS26176</p>
            </div>
          </div>
        </div>

        {/* Landing Centre Board */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col">
          <div className="bg-gray-50 p-3 border-b flex items-center justify-between">
            <h3 className="font-bold flex items-center text-gray-700"><Monitor className="w-4 h-4 mr-2" /> Landing Centre Board (1080p)</h3>
          </div>
          <div className="p-4 flex-1 bg-black text-white flex flex-col">
            <h2 className="text-3xl font-black text-center mb-4 text-red-500 uppercase tracking-widest">DO NOT CROSS</h2>
            <div className="grid grid-cols-2 gap-4 flex-1">
              <div className="border-2 border-red-900 rounded p-4 flex flex-col justify-center items-center text-center">
                <span className="text-4xl font-bold text-red-500 mb-2">FRP Skiffs</span>
                <span className="text-xl font-bold uppercase">Prohibited</span>
              </div>
              <div className="border-2 border-amber-900 rounded p-4 flex flex-col justify-center items-center text-center">
                <span className="text-4xl font-bold text-amber-500 mb-2">Trawlers</span>
                <span className="text-xl font-bold uppercase">Caution</span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
