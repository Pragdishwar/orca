import React, { useEffect, useRef, useState } from 'react';
import {
  Clock, MapPin, Send, Ship, TriangleAlert, X, Mic
} from 'lucide-react';
import { useOrcaStore } from '../../store/useOrcaStore';
import { VerdictBadge } from '../ui/Primitives';
import type { QueryResponse } from '../../api/client';

const CHIP_META: Record<string, { Icon: React.ElementType; label: string; field: string }> = {
  location: { Icon: MapPin, label: 'Location', field: 'location' },
  time_window: { Icon: Clock, label: 'When', field: 'time_label' },
  boat: { Icon: Ship, label: 'Boat', field: 'hull_class' },
};

/** FR-04: retained context is visible, and the field that changed flashes. */
function ContextChips() {
  const { context, updatedFields, clearContextField } = useOrcaStore();
  const entries = Object.entries(CHIP_META).filter(
    ([, meta]) => context[meta.field]);

  if (!entries.length) {
    return <p className="text-xs text-slate-400">No context retained yet.</p>;
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {entries.map(([key, meta]) => {
        const flash = updatedFields.includes(key);
        return (
          <span
            key={key}
            title={`${meta.label} carried across turns`}
            className={`inline-flex items-center gap-1 rounded-full border px-2 py-1
              text-xs font-medium transition-colors ${flash
                ? 'animate-pulse border-sky-400 bg-sky-100 text-sky-900'
                : 'border-slate-300 bg-white text-slate-700'}`}
          >
            <meta.Icon className="h-3 w-3" aria-hidden />
            {String(context[meta.field]).replace(/_/g, ' ')}
            <button
              onClick={() => clearContextField(meta.field)}
              aria-label={`Clear ${meta.label}`}
              className="ml-0.5 rounded-full p-0.5 hover:bg-slate-200"
            >
              <X className="h-3 w-3" aria-hidden />
            </button>
          </span>
        );
      })}
    </div>
  );
}

function AnswerCard({ res }: { res: QueryResponse }) {
  const rejected = res.guard.result === 'REJECT';
  const isAlt = !!res.intent_result;
  
  return (
    <div className={`w-full rounded-xl border bg-white p-4 shadow-sm ${rejected
      ? 'border-red-300' : 'border-slate-200'}`}>
      
      {!isAlt && (
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
          <VerdictBadge verdict={res.verdict} />
          <span className="font-mono text-[10px] text-slate-500">
            {res.hull_label} · {res.date}
          </span>
        </div>
      )}

      {rejected && (
        <div className="mb-3 flex items-start gap-2 rounded-lg border border-red-300
          bg-red-50 p-3 text-xs text-red-900">
          <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          <span>
            <strong>Guard rejected this advisory ({res.guard.reason}).</strong> The
            generated text contradicted the computed verdict, so the official bulletin is
            shown below instead.
          </span>
        </div>
      )}

      <p className="mb-3 text-sm leading-relaxed text-slate-800">{res.answer}</p>

      {res.intent_result?.points && (
        <ul className="mb-3 space-y-1">
          {res.intent_result.points.map((p) => (
            <li key={p.pfz_id} className="flex items-center gap-2 rounded border
              border-emerald-200 bg-emerald-50 px-2 py-1 text-xs text-emerald-900">
              <span className="font-mono font-bold">{p.pfz_id}</span>
              <span>{p.distance_km} km</span>
              <span className="text-emerald-700">bearing {p.bearing_deg}°</span>
              <span className="ml-auto text-emerald-700">{p.depth_m} m deep</span>
            </li>
          ))}
        </ul>
      )}

      {res.intent_result?.zones && (
        <ul className="mb-3 space-y-1">
          {res.intent_result.zones.filter((z) => z.status !== 'CLEAR').map((z) => (
            <li key={z.name} className="flex items-center gap-2 rounded border
              border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-900">
              <span className="font-bold">{z.status}</span>
              <span>{z.name}</span>
              <span className="ml-auto">{z.distance_km} km · {z.type}</span>
            </li>
          ))}
        </ul>
      )}

      {isAlt ? (
        <details className="mt-4 border-t border-slate-200 pt-3 text-[11px] text-slate-500">
          <summary className="cursor-pointer mb-2 font-medium">
            Show background crossing context (always computed)
          </summary>
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <VerdictBadge verdict={res.verdict} />
            <span className="font-mono text-[10px] text-slate-500">
              {res.hull_label} · {res.date}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <Cell label="Hazard" value={res.index_value.toFixed(3)} />
            <Cell
              label="Return"
              value={res.return_window
                ? `${res.return_window.start_label}-${res.return_window.end_label}`
                : 'none'}
            />
            <Cell label="Turn back" value={res.turn_back_time ?? 'n/a'} />
          </div>
        </details>
      ) : (
        <div className="grid grid-cols-2 gap-2 text-xs">
          <Cell label="Hazard" value={res.index_value.toFixed(3)} />
          <Cell
            label="Return"
            value={res.return_window
              ? `${res.return_window.start_label}-${res.return_window.end_label}`
              : 'none'}
          />
          <Cell label="Turn back" value={res.turn_back_time ?? 'n/a'} />
        </div>
      )}

      {res.date_mapped_from_request && (
        <p className="mt-3 text-[11px] italic text-slate-500">
          The analysis record covers 2022–2024, so this answer uses the same calendar day
          in the most recent record year.
        </p>
      )}
    </div>
  );
}

function Cell({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-slate-200 bg-slate-50 p-2">
      <div className="text-[10px] font-bold uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-0.5 font-mono text-sm text-slate-900">{value}</div>
    </div>
  );
}

export default function ConversationPane() {
  const {
    chatHistory, isQuerying, submitQuery, personas, persona, setPersona,
    useMockChat, setUseMockChat
  } = useOrcaStore();
  const [text, setText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory.length, isQuerying]);

  useEffect(() => {
    // @ts-ignore
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      
      recognitionRef.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setText(transcript);
      };
      
      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
  }, []);

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      recognitionRef.current?.start();
      setIsListening(true);
    }
  };

  const activePersona = personas.find((p) => p.persona_id === persona);
  const suggestions = activePersona?.suggested_queries ?? [];

  const send = (value?: string) => {
    const q = (value ?? text).trim();
    if (!q || isQuerying) return;
    submitQuery(q);
    setText('');
  };

  return (
    <div className="flex h-full flex-col min-h-0 flex-1">
      <div className="border-b border-slate-200 bg-slate-50 p-3 shrink-0">
        <div className="mb-2 flex items-center justify-between gap-2">
          <h3 className="text-[11px] font-bold uppercase tracking-wide text-slate-500">
            Retained context
          </h3>
          <div className="flex gap-2">
            <button
              onClick={() => setUseMockChat(!useMockChat)}
              className={`text-xs px-2 py-1 rounded border ${useMockChat ? 'bg-amber-100 border-amber-300 text-amber-800' : 'bg-slate-200 border-slate-300 text-slate-700'}`}
              title="Toggle real-time streaming"
            >
              Streaming {useMockChat ? 'OFF' : 'ON'}
            </button>
            <select
              aria-label="Persona"
              value={persona}
              onChange={(e) => setPersona(e.target.value)}
              className="rounded border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700 outline-none focus:ring-2 focus:ring-sky-500"
            >
              {personas.length === 0 && <option value="fisherman">Fisherman</option>}
              {personas.map((p) => (
                <option key={p.persona_id} value={p.persona_id}>{p.label}</option>
              ))}
            </select>
          </div>
        </div>
        <ContextChips />
        {activePersona && (
          <p className="mt-2 text-[11px] italic text-slate-500">
            {activePersona.answer_framing}
          </p>
        )}
      </div>

      <div className="flex-1 space-y-3 overflow-y-scroll bg-slate-50 p-3 min-h-0">
        {chatHistory.length === 0 && !isQuerying && (
          <div className="space-y-3">
            <p className="pt-4 text-center text-sm text-slate-500">
              Ask about crossing the Muthalapozhi bar.
            </p>
            <div className="grid gap-2">
              {suggestions.map((q) => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="rounded-lg border border-slate-200 bg-white p-2.5 text-left
                    text-xs text-slate-700 hover:border-sky-300 hover:bg-sky-50"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {chatHistory.map((m) => (
          <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : ''}`}>
            {m.role === 'user' ? (
              <div className="max-w-[85%] rounded-xl rounded-tr-sm bg-sky-600 px-3 py-2
                text-sm text-white shadow-sm">
                {m.text}
              </div>
            ) : m.error ? (
              <div className="w-full rounded-xl border border-red-300 bg-red-50 p-3
                text-sm text-red-900">
                {m.text}
              </div>
            ) : m.response ? (
              <AnswerCard res={m.response} />
            ) : (
              <div className="rounded-xl border border-slate-200 bg-white p-3 text-sm">
                {m.text}
              </div>
            )}
          </div>
        ))}

        {isQuerying && (
          <div className="inline-flex items-center gap-2 rounded-xl border border-slate-200
            bg-white px-3 py-2 text-sm text-slate-500">
            <span className="h-2 w-2 animate-ping rounded-full bg-sky-500" />
            Planner → Discovery → Risk → Guard…
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="border-t border-slate-200 bg-white p-3 shrink-0">
        <div className="flex items-end gap-2 rounded-xl border border-slate-200
          bg-slate-100 p-1.5">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
            }}
            rows={1}
            aria-label="Ask ORCA"
            placeholder="Is it safe to go out tomorrow morning?"
            className="min-h-[2.5rem] flex-1 resize-none bg-transparent px-2 py-2 text-sm
              text-slate-800 outline-none"
          />
          <button
            onClick={toggleListening}
            aria-label={isListening ? "Stop listening" : "Start listening"}
            className={`rounded-full p-2.5 shadow-sm transition-colors ${
              isListening 
                ? 'bg-red-500 text-white hover:bg-red-600 animate-pulse' 
                : 'bg-slate-200 text-slate-600 hover:bg-slate-300'
            }`}
          >
            <Mic className="h-4 w-4" aria-hidden />
          </button>
          <button
            onClick={() => send()}
            disabled={isQuerying || !text.trim()}
            aria-label="Send"
            className="rounded-full bg-sky-600 p-2.5 text-white shadow-sm
              hover:bg-sky-700 disabled:bg-slate-300 disabled:text-slate-500"
          >
            <Send className="h-4 w-4" aria-hidden />
          </button>
        </div>
        <p className="mt-1.5 text-[10px] text-slate-400">
          Answers are composed in English by default but will be automatically translated to Malayalam or Tamil if you ask in those languages.
        </p>
      </div>
    </div>
  );
}
