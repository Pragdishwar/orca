import React from 'react';
import ConversationPane from '../components/platform/ConversationPane';
import MapPane from '../components/platform/MapPane';
import EvidencePane from '../components/platform/EvidencePane';
import { useOrcaStore } from '../store/useOrcaStore';
import { VerdictBadge } from '../components/ui/Primitives';

/**
 * FR-13: identical conditions, different verdicts by hull class. This strip is
 * the clearest evidence that the boat profile, not just the weather, decides
 * the answer.
 */
function HullStrip() {
  const active = useOrcaStore((s) => s.active);
  if (!active?.hull_comparison?.length) return null;

  return (
    <section className="mb-3 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
      <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-sm font-bold text-slate-800">
          Same conditions, every hull class
        </h3>
        <p className="text-xs text-slate-500">
          {active.date} · index{' '}
          <span className="font-mono font-semibold">{active.index_value.toFixed(3)}</span>
          {' '}for all four — only the threshold differs
        </p>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {active.hull_comparison.map((h) => {
          const isActive = h.hull_class === active.hull_class;
          return (
            <div
              key={h.hull_class}
              className={`rounded-lg border p-2.5 ${isActive
                ? 'border-sky-400 bg-sky-50 ring-1 ring-sky-300'
                : 'border-slate-200'}`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-bold text-slate-800">{h.hull_label}</span>
                {isActive && (
                  <span className="rounded bg-sky-600 px-1.5 py-0.5 text-[9px]
                    font-bold text-white">ASKED</span>
                )}
              </div>
              <div className="mt-1.5"><VerdictBadge verdict={h.verdict} size="sm" /></div>
              <div className="mt-1.5 font-mono text-[10px] text-slate-500">
                marginal {h.index_marginal} · unsafe {h.index_unsafe}
              </div>
              <div className="mt-0.5 text-[10px] text-slate-500">
                turn back {h.turn_back_label ?? 'n/a'}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default function PlatformTab() {
  return (
    <div className="flex flex-col h-full">
      <HullStrip />
      <div className="flex flex-col lg:grid lg:h-[calc(100vh-12rem)] lg:min-h-[40rem] gap-3
        lg:grid-cols-[minmax(0,0.75fr)_minmax(0,2.2fr)_minmax(0,0.85fr)] flex-1">
        <div className="flex flex-col overflow-hidden rounded-xl border border-slate-200
          bg-white shadow-sm min-h-[30rem] lg:min-h-0">
          <ConversationPane />
        </div>
        <div className="min-h-[24rem] lg:min-h-0 overflow-hidden rounded-xl border border-slate-200
          bg-slate-100 shadow-sm flex flex-col">
          <MapPane />
        </div>
        <div className="flex flex-col overflow-hidden rounded-xl border border-slate-200
          bg-white shadow-sm min-h-[30rem] lg:min-h-0">
          <EvidencePane />
        </div>
      </div>
    </div>
  );
}
