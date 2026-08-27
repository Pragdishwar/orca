import React, { useState } from 'react';
import { useOrcaStore } from '../../store/useOrcaStore';
import { Mic, Send, X, AlertTriangle, ShieldCheck, Clock, MapPin, Zap } from 'lucide-react';

export default function ConversationPane() {
  const { persona } = useOrcaStore();
  const [context, setContext] = useState({ location: 'Muthalapozhi', time: 'Tomorrow 08:00', boat: 'B-XYZ' });
  const [isRecording, setIsRecording] = useState(false);
  const [query, setQuery] = useState('');
  
  const removeContext = (key: keyof typeof context) => setContext({ ...context, [key]: '' });

  return (
    <div className="flex flex-col h-full relative">
      {/* Top Context Bar */}
      <div className="bg-slate-50 border-b p-3">
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-xs font-bold text-gray-500 uppercase">Current Context</h3>
          <select className="text-xs bg-white border rounded px-2 py-1 outline-none">
            <option>Fisherman Persona</option>
            <option>Coast Guard Persona</option>
          </select>
        </div>
        <div className="flex flex-wrap gap-2">
          {context.location && (
            <div className="flex items-center bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full animate-pulse-once">
              <MapPin className="w-3 h-3 mr-1" /> {context.location}
              <X className="w-3 h-3 ml-1 cursor-pointer" onClick={() => removeContext('location')} />
            </div>
          )}
          {context.time && (
            <div className="flex items-center bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full animate-pulse-once">
              <Clock className="w-3 h-3 mr-1" /> {context.time}
              <X className="w-3 h-3 ml-1 cursor-pointer" onClick={() => removeContext('time')} />
            </div>
          )}
        </div>
      </div>

      {/* Turn History List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {/* User Query */}
        <div className="flex justify-end">
          <div className="bg-blue-600 text-white p-3 rounded-xl rounded-tr-sm max-w-[85%] shadow-sm text-sm">
            Is it safe to go out to Wadge Bank tomorrow morning?
          </div>
        </div>
        
        {/* Answer Card */}
        <div className="flex justify-start">
          <div className="bg-white border border-red-200 p-4 rounded-xl rounded-tl-sm max-w-[95%] shadow-sm w-full">
            <div className="flex items-center justify-between mb-3 border-b pb-3">
              <div className="flex items-center text-red-600 font-black text-lg tracking-tight">
                <AlertTriangle className="w-5 h-5 mr-2" /> DO NOT CROSS
              </div>
              <span className="bg-gray-100 text-gray-500 text-xs px-2 py-1 rounded font-mono">ORCA ENGINE</span>
            </div>
            
            <p className="text-sm text-gray-700 mb-4 font-medium leading-relaxed">
              Conditions are highly hazardous. A 4.0m swell is approaching the inlet during peak ebb tide, creating severe breaking waves in the channel.
            </p>
            
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-red-50 p-2 rounded border border-red-100">
                <span className="block text-red-400 font-bold mb-1">RETURN WINDOW</span>
                <span className="text-red-900 font-mono text-sm">CLOSED</span>
              </div>
              <div className="bg-red-50 p-2 rounded border border-red-100">
                <span className="block text-red-400 font-bold mb-1">TURN-BACK TIME</span>
                <span className="text-red-900 font-mono text-sm">N/A</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Input Box */}
      <div className="p-3 bg-white border-t relative">
        {/* Quick Queries (when empty) */}
        {!query && (
          <div className="absolute bottom-16 left-3 right-3 grid grid-cols-2 gap-2">
            <button className="text-xs bg-gray-50 hover:bg-gray-100 text-gray-600 p-2 rounded text-left border">Check waves tomorrow</button>
            <button className="text-xs bg-gray-50 hover:bg-gray-100 text-gray-600 p-2 rounded text-left border">PFZ for Quilon Bank</button>
            <button className="text-xs bg-gray-50 hover:bg-gray-100 text-gray-600 p-2 rounded text-left border">Are alerts active?</button>
            <button className="text-xs bg-gray-50 hover:bg-gray-100 text-gray-600 p-2 rounded text-left border">IMBL distance check</button>
          </div>
        )}

        <div className="flex items-center bg-gray-100 rounded-xl p-1 shadow-inner border border-gray-200">
          <button 
            onClick={() => setIsRecording(!isRecording)}
            className={`p-3 rounded-full transition-colors ${isRecording ? 'bg-red-500 text-white animate-pulse' : 'text-gray-500 hover:bg-gray-200'}`}
          >
            <Mic className="w-5 h-5" />
          </button>
          
          <div className="flex-1 px-2 relative">
            <textarea 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask for marine advisory..."
              className="w-full bg-transparent outline-none resize-none text-sm py-3 text-gray-800"
              rows={1}
            />
            {/* Lang auto-detect indicator */}
            <span className="absolute right-2 top-3 text-[10px] font-bold text-gray-400">EN</span>
          </div>
          
          <button className="p-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors shadow-sm mx-1">
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
