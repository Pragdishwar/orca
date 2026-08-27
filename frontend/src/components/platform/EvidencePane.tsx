import React, { useState } from 'react';
import {
  ChevronDown, ChevronRight, Network, Plus, Server, ShieldAlert, Zap,
} from 'lucide-react';
import { useOrcaStore } from '../../store/useOrcaStore';
import { api } from '../../api/client';
import { AccessBadge, EmptyState, ProvenanceBadge } from '../ui/Primitives';

type Sub = 'trace' | 'sources' | 'registry' | 'limits';

const LIMITS = [
  {
    title: 'Calibration scope',
    body: 'The index is calibrated to the geometry of the Muthalapozhi mouth alone '
      + '(8.636° N, 76.786° E), with a measured channel bearing of 250°. It does not '
      + 'generalise to another inlet without recalibration.',
  },
  {
    title: 'No bathymetry',
    body: 'There is no depth model for the bar. Sandbar migration, which is the dominant '
      + 'control on where and when waves break at this mouth, is not represented at all.',
  },
  {
    title: 'No breaking simulation',
    body: 'The index scores offshore wave state and tide. It does not simulate wave '
      + 'breaking or run-up in the channel, which is the mechanism that actually '
      + 'capsizes boats.',
  },
  {
    title: 'Product resolution',
    body: 'The wave source resolves conditions on a coarse grid several kilometres '
      + 'offshore. Short-period chop generated inside the channel is invisible to it — '
      + 'this is the documented cause of the published failure case.',
  },
  {
    title: 'Elicited thresholds',
    body: 'Hull thresholds (D-10) are judgement calls about vulnerability, not values '
      + 'fitted to the incident record. They are marked source=elicited throughout.',
  },
  {
    title: 'Ground truth and exposure',
    body: 'Validation is scored against an incident list with no record of how many '
      + 'boats crossed on a given day, so a correct negative may only mean nobody '
      + 'sailed. The record itself is synthetic.',
  },
];

export default function EvidencePane() {
  const [sub, setSub] = useState<Sub>('trace');
  const { trace, active, sources, sourcesRule } = useOrcaStore();

  const tabs: { id: Sub; label: string; Icon: React.ElementType }[] = [
    { id: 'trace', label: 'Trace', Icon: Network },
    { id: 'sources', label: 'Sources', Icon: Server },
    { id: 'registry', label: 'Registry', Icon: Plus },
    { id: 'limits', label: 'Limits', Icon: ShieldAlert },
  ];

  return (
    <div className="flex h-full flex-col bg-white">
      <div className="flex border-b border-slate-200 bg-slate-50">
        {tabs.map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => setSub(id)}
            className={`flex-1 py-2.5 text-[10px] font-bold uppercase tracking-wide
              ${sub === id
                ? 'border-b-2 border-sky-600 text-sky-700'
                : 'text-slate-500 hover:text-slate-800'}`}
          >
            <Icon className="mx-auto mb-1 h-4 w-4" aria-hidden />
            {label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {sub === 'trace' && <TraceView />}
        {sub === 'sources' && <SourcesView sources={sources} rule={sourcesRule} />}
        {sub === 'registry' && <RegistryView />}
        {sub === 'limits' && <LimitsView />}
      </div>

      {active && sub === 'trace' && (
        <div className="border-t border-slate-200 bg-slate-50 px-3 py-2 text-[10px]
          text-slate-500">
          trace {active.trace_id.slice(0, 8)} · {trace.length} nodes ·{' '}
          {trace.reduce((a, s) => a + s.ms, 0).toFixed(1)} ms total
        </div>
      )}
    </div>
  );
}

function TraceView() {
  const { trace, isQuerying } = useOrcaStore();
  const [open, setOpen] = useState<string | null>(null);

  if (isQuerying) {
    return <p className="text-sm text-slate-500">Running agents…</p>;
  }
  if (!trace.length) {
    return <EmptyState title="Ask a question" hint="The reasoning trace appears here." />;
  }

  const hinges = trace.filter((s) => s.hinge).length;

  return (
    <>
      <div className="mb-3 rounded-lg border border-slate-200 bg-slate-50 p-2.5">
        <h4 className="text-xs font-bold text-slate-800">How this answer was reached</h4>
        <p className="mt-1 text-[11px] leading-relaxed text-slate-600">
          Each row is one agent, with what it was given and what it returned. Click a row
          to see both. Nothing here is a summary written after the fact — it is what
          actually ran.
        </p>
        <p className="mt-1.5 text-[11px] leading-relaxed text-amber-900">
          <strong>Amber rows are hinges</strong>{hinges ? ` (${hinges} here)` : ''}: points
          where one agent's output changed another's decision. Each is verified by
          recomputing with that one input removed — if the verdict would not have changed,
          no hinge is claimed.
        </p>
      </div>

    <ol className="relative ml-3 space-y-3 border-l-2 border-slate-200">
      {trace.map((step, i) => {
        const id = `${step.agent}-${i}`;
        const expanded = open === id;
        return (
          <li key={id} className="relative pl-5">
            <span className={`absolute -left-[9px] top-1 h-4 w-4 rounded-full border-2
              ${step.hinge ? 'border-amber-500 bg-amber-400'
                : 'border-emerald-500 bg-white'}`} />

            <button
              onClick={() => setOpen(expanded ? null : id)}
              className="flex w-full items-center gap-1.5 text-left"
            >
              {expanded ? <ChevronDown className="h-3.5 w-3.5 text-slate-400" aria-hidden />
                : <ChevronRight className="h-3.5 w-3.5 text-slate-400" aria-hidden />}
              <span className="text-sm font-bold text-slate-800">{step.agent}</span>
              <span className="ml-auto font-mono text-[10px] text-slate-400">
                {step.ms.toFixed(1)} ms
              </span>
            </button>

            {step.hinge && (
              <div className="mt-1.5 rounded-lg border border-amber-300 bg-amber-50 p-2.5">
                <div className="mb-1 flex items-center gap-1 text-xs font-bold
                  text-amber-900">
                  <Zap className="h-3.5 w-3.5" aria-hidden />
                  HINGE · {step.hinge.type.replace(/_/g, ' ')}
                </div>
                <p className="text-[11px] leading-relaxed text-amber-950">
                  {step.hinge.cause}
                </p>
              </div>
            )}

            {expanded && (
              <div className="mt-1.5 space-y-1.5">
                <KV title="input" data={step.input} />
                <KV title="output" data={step.output} />
              </div>
            )}
          </li>
        );
      })}
    </ol>
    </>
  );
}

function KV({ title, data }: { title: string; data: Record<string, unknown> }) {
  return (
    <div className="rounded border border-slate-200 bg-slate-50 p-2">
      <div className="mb-1 text-[9px] font-bold uppercase tracking-wide text-slate-400">
        {title}
      </div>
      <dl className="space-y-0.5">
        {Object.entries(data ?? {}).map(([k, v]) => (
          <div key={k} className="flex gap-2 text-[11px]">
            <dt className="shrink-0 font-medium text-slate-500">{k}</dt>
            <dd className="ml-auto break-all text-right font-mono text-slate-800">
              {typeof v === 'object' ? JSON.stringify(v) : String(v)}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function SourcesView({ sources, rule }: { sources: any[]; rule: string }) {
  const active = useOrcaStore((s) => s.active);
  const perVariable = active?.discovery_log.per_variable ?? [];

  return (
    <div className="space-y-3">
      <p className="rounded border border-sky-200 bg-sky-50 p-2 text-[11px] text-sky-900">
        {rule || 'Indian/ISRO sources are attempted before any non-Indian substitute.'}
      </p>

      {perVariable.length > 0 && (
        <div className="rounded-lg border border-slate-200 p-2.5">
          <h4 className="mb-1.5 text-[11px] font-bold uppercase tracking-wide text-slate-500">
            Selection, per variable
          </h4>
          <div className="space-y-1.5">
            {perVariable.map((p) => (
              <div key={p.variable} className="text-[11px]">
                <span className="font-mono font-bold text-slate-800">{p.variable}</span>
                <span className="text-slate-500"> · tried </span>
                <span className="text-slate-700">{p.attempted_first ?? '—'}</span>
                {p.failed.length > 0 && (
                  <span className="text-orange-700"> (failed: {p.failed.join(', ')})</span>
                )}
                <span className="text-slate-500"> → </span>
                <span className="font-semibold text-emerald-700">
                  {p.chosen ?? 'unavailable'}
                </span>
                {p.priority_tier && (
                  <span className="text-slate-400"> tier {p.priority_tier}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {sources.length === 0 && <EmptyState title="Source list unavailable" />}

      {[1, 2, 3].map((tier) => {
        const rows = sources.filter((s) => s.priority_tier === tier);
        if (!rows.length) return null;
        return (
          <div key={tier}>
            <h4 className="mb-1.5 text-[10px] font-bold uppercase tracking-wide
              text-slate-500">
              {tier === 1 ? 'Tier 1 · Indian / ISRO'
                : tier === 2 ? 'Tier 2 · International' : 'Tier 3 · Fallback'}
            </h4>
            <div className="space-y-1.5">
              {rows.map((s) => (
                <div key={s.source_id}
                  className={`rounded-lg border p-2.5 ${s.access_status === 'CONNECTED'
                    ? 'border-slate-200' : 'border-slate-200 bg-slate-50'}`}>
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="text-xs font-bold text-slate-800">{s.provider}</div>
                      <div className="text-[10px] text-slate-500">
                        {s.country} · {s.resolution_km} km
                      </div>
                    </div>
                    <AccessBadge status={s.access_status} />
                  </div>
                  <div className="mt-1.5 flex flex-wrap items-center gap-1">
                    {(Array.isArray(s.variables) ? s.variables : []).map((v: string) => (
                      <span key={v} className="rounded bg-slate-100 px-1 py-0.5
                        font-mono text-[9px] text-slate-600">{v}</span>
                    ))}
                    <span className="ml-auto"><ProvenanceBadge value={s.provenance} /></span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/** FR-08: add a source here and the next query ranks it, with no code change. */
function RegistryView() {
  const [form, setForm] = useState({
    source_id: '', provider: '', country: 'IN', variables: 'hs,tp,dir,swell_hs',
    resolution_km: 5, priority_tier: 1, access_status: 'CONNECTED',
  });
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      await api.addSource({
        source_id: form.source_id.trim(),
        provider: form.provider.trim(),
        country: form.country.trim(),
        variables: form.variables.split(',').map((v) => v.trim()).filter(Boolean),
        spatial_coverage: 'kerala',
        resolution_km: Number(form.resolution_km),
        access_method: 'manual_entry',
        access_status: form.access_status,
        priority_tier: Number(form.priority_tier),
      });
      setMsg({
        ok: true,
        text: 'Added. Ask another question — the discovery agent will rank it '
          + 'immediately, with no restart.',
      });
      useOrcaStore.getState().boot();
    } catch (err) {
      setMsg({ ok: false, text: err instanceof Error ? err.message : 'Failed' });
    } finally {
      setBusy(false);
    }
  };

  const field = 'w-full rounded border border-slate-300 px-2 py-1 text-xs outline-none '
    + 'focus:ring-2 focus:ring-sky-500';

  return (
    <form onSubmit={submit} className="space-y-2">
      <p className="text-[11px] text-slate-600">
        Registry entries are data, not code. Adding one changes what the discovery agent
        selects on the next query.
      </p>
      <input required className={field} placeholder="source_id"
        value={form.source_id}
        onChange={(e) => setForm({ ...form, source_id: e.target.value })} />
      <input required className={field} placeholder="Provider name"
        value={form.provider}
        onChange={(e) => setForm({ ...form, provider: e.target.value })} />
      <input className={field} placeholder="Variables (comma separated)"
        value={form.variables}
        onChange={(e) => setForm({ ...form, variables: e.target.value })} />
      <div className="grid grid-cols-3 gap-2">
        <input className={field} placeholder="Country" value={form.country}
          onChange={(e) => setForm({ ...form, country: e.target.value })} />
        <input className={field} type="number" step="0.1" placeholder="km"
          value={form.resolution_km}
          onChange={(e) => setForm({ ...form, resolution_km: +e.target.value })} />
        <select className={field} value={form.priority_tier}
          onChange={(e) => setForm({ ...form, priority_tier: +e.target.value })}>
          <option value={1}>Tier 1</option>
          <option value={2}>Tier 2</option>
          <option value={3}>Tier 3</option>
        </select>
      </div>
      <select className={field} value={form.access_status}
        onChange={(e) => setForm({ ...form, access_status: e.target.value })}>
        <option value="CONNECTED">CONNECTED</option>
        <option value="ATTEMPTED">ATTEMPTED</option>
        <option value="SUBSTITUTED">SUBSTITUTED</option>
      </select>
      <button disabled={busy}
        className="w-full rounded bg-sky-600 py-1.5 text-xs font-bold text-white
          hover:bg-sky-700 disabled:bg-slate-300">
        {busy ? 'Adding…' : 'Add source to registry'}
      </button>
      {msg && (
        <p className={`rounded border p-2 text-[11px] ${msg.ok
          ? 'border-emerald-300 bg-emerald-50 text-emerald-900'
          : 'border-red-300 bg-red-50 text-red-900'}`}>
          {msg.text}
        </p>
      )}
    </form>
  );
}

function LimitsView() {
  return (
    <div className="space-y-2">
      <p className="rounded border border-violet-200 bg-violet-50 p-2 text-[11px]
        text-violet-900">
        <strong>All data in this prototype is synthetic.</strong> It is generated to match
        the schema and seasonal behaviour of the real products, so the ETL can replace it
        wholesale — but no number here is an observation.
      </p>
      {LIMITS.map((l) => (
        <div key={l.title} className="rounded-lg border border-slate-200 p-2.5">
          <h4 className="text-xs font-bold text-slate-800">{l.title}</h4>
          <p className="mt-1 text-[11px] leading-relaxed text-slate-600">{l.body}</p>
        </div>
      ))}
    </div>
  );
}
