import React, { useEffect, useRef, useState } from 'react';
import {
  AlertOctagon, Lock, SlidersHorizontal, UserCheck,
} from 'lucide-react';
import { api, Validation } from '../api/client';
import { useOrcaStore } from '../store/useOrcaStore';
import {
  ErrorState, Metric, Panel, Spinner, VerdictBadge,
} from '../components/ui/Primitives';

const pct = (v: number) => `${(v * 100).toFixed(1)}%`;

const PRIVACY = [
  'A boat profile stores a ground *name*. Coordinates live on the ground record, never '
  + 'against a boat — verifiable by inspecting the schema.',
  'No continuous position logging. There is no table that could hold a track.',
  'Trip fields linked to an advisory are purged on safe return.',
  'No export path to any third party exists in this build.',
];

export default function TrustTab() {
  const { active, submitQuery, setActiveTab } = useOrcaStore();
  const [threshold, setThreshold] = useState(0.44);
  const [data, setData] = useState<Validation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [recomputing, setRecomputing] = useState(false);
  const [officer, setOfficer] = useState('');
  const [roster, setRoster] = useState<
    { officer_id: string; name: string; role: string }[]>([]);
  const [release, setRelease] = useState<{ ok: boolean; text: string } | null>(null);
  const [modes, setModes] = useState<{ id: string; label: string; rule: string;
    effect: string }[]>([]);
  const timer = useRef<number | null>(null);

  const load = (t: number) => {
    setRecomputing(true);
    setError(null);
    api.validation(t)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setRecomputing(false));
  };

  useEffect(() => {
    load(threshold);
    api.degradationModes().then((d) => setModes(d.modes)).catch(() => setModes([]));
    api.officers().then((d) => setRoster(d.officers)).catch(() => setRoster([]));
  }, []);

  // Debounce: the slider recomputes the whole record server-side.
  const onSlide = (v: number) => {
    setThreshold(v);
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => load(v), 250);
  };

  const doRelease = async () => {
    if (!active?.advisory_id || !officer.trim()) return;
    try {
      const r = await api.releaseAdvisory(active.advisory_id, officer.trim());
      setRelease({ ok: true, text: `State is now ${r.state}, released by ${r.released_by}.` });
    } catch (e) {
      setRelease({ ok: false, text: e instanceof Error ? e.message : 'Release failed' });
    }
  };

  const forceFailure = async () => {
    setActiveTab('platform');
    await submitQuery('Is it safe to cross tomorrow?', { forceFailure: true });
  };

  const user = useOrcaStore((s) => s.user);

  return (
    <div className="mx-auto max-w-5xl space-y-4">
      <Panel
        title="Community threshold"
        subtitle="Move the operating point and POD/FAR are recomputed over the whole record"
        right={recomputing ? <Spinner label="Recomputing…" /> : null}
      >
        {error ? <ErrorState message={error} onRetry={() => load(threshold)} /> : (
          <>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-medium text-slate-700">
                Hazard index alerting threshold
              </span>
              <span className="rounded-full bg-sky-100 px-3 py-1 font-mono font-bold
                text-sky-900">
                {threshold.toFixed(2)}
              </span>
            </div>
            <input
              type="range" min={0.2} max={0.8} step={0.01}
              value={threshold}
              onChange={(e) => onSlide(parseFloat(e.target.value))}
              aria-label="Hazard index threshold"
              className="w-full accent-sky-600"
            />
            <div className="mt-1 flex justify-between text-[10px] font-semibold uppercase
              text-slate-400">
              <span>Risk averse · more false alarms</span>
              <span>Risk tolerant · more misses</span>
            </div>

            {data && (
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <Metric label="POD" value={pct(data.contingency.pod)} tone="good"
                  sub={`${data.contingency.hits}/${data.contingency.event_count} caught`} />
                <Metric label="FAR" value={pct(data.contingency.far)} tone="warn"
                  sub={`${data.contingency.false_alarms} false alarms`} />
                <Metric label="Days flagged / yr"
                  value={data.contingency.days_per_year.toFixed(0)}
                  sub={`${data.contingency.misses} incidents missed`} />
              </div>
            )}
            <p className="mt-3 text-xs text-slate-500">
              This is a real recomputation over {data?.record.days ?? '—'} days, not an
              interpolated curve. Tightening the threshold always trades misses for false
              alarms — the community chooses where on that trade to sit.
            </p>
          </>
        )}
      </Panel>

      <Panel title="Human release" subtitle="R-4 · nothing publishes without a name on it">
        {user?.role !== 'admin' ? (
          <p className="text-sm text-slate-500">
            You do not have permission to release advisories. This action is restricted to authorised officers.
          </p>
        ) : !active ? (
          <p className="text-sm text-slate-500">
            No active advisory. Ask a question on the Platform tab first.
          </p>
        ) : (
          <>
            <div className="mb-3 flex flex-wrap items-center gap-3">
              <VerdictBadge verdict={active.verdict} />
              <span className="rounded bg-slate-100 px-2 py-1 text-xs font-bold
                text-slate-700">
                {active.guard.result === 'REJECT' ? 'REJECTED BY GUARD' : 'PENDING RELEASE'}
              </span>
            </div>
            <div className="flex flex-wrap items-end gap-3">
              <label className="min-w-[14rem] flex-1">
                <span className="text-xs font-bold uppercase text-slate-500">
                  Step 1 — Authorising officer (R-4)
                </span>
                <select
                  value={officer}
                  onChange={(e) => setOfficer(e.target.value)}
                  className="mt-1 w-full rounded border border-slate-300 bg-white px-3
                    py-2 text-sm outline-none focus:ring-2 focus:ring-sky-500"
                >
                  <option value="">Select an authorised officer…</option>
                  {roster.map((o) => (
                    <option key={o.officer_id} value={o.officer_id}>
                      {o.name} · {o.officer_id}
                    </option>
                  ))}
                </select>
              </label>
              <button
                onClick={doRelease}
                disabled={!officer.trim()}
                className="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2
                  text-sm font-bold text-white hover:bg-sky-700 disabled:bg-slate-300
                  disabled:text-slate-500"
              >
                <UserCheck className="h-4 w-4" aria-hidden />
                {officer.trim() ? 'Release advisory' : 'Release — name needed'}
              </button>
            </div>
            {release && (
              <p className={`mt-3 rounded border p-2.5 text-sm ${release.ok
                ? 'border-emerald-300 bg-emerald-50 text-emerald-900'
                : 'border-red-300 bg-red-50 text-red-900'}`}>
                {release.text}
              </p>
            )}
          </>
        )}
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Privacy" subtitle="R-6 · named grounds only">
          <ul className="space-y-2 text-sm text-slate-700">
            {PRIVACY.map((p) => (
              <li key={p} className="flex gap-2">
                <Lock className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" aria-hidden />
                {p}
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title="Guard demonstration" subtitle="FR-18 · force a real contradiction">
          <p className="mb-3 text-sm text-slate-600">
            This does not fake a rejection. It makes the Synthesis node emit a verdict
            token that contradicts the computed verdict; the deterministic comparator then
            catches it and publishes the official bulletin instead.
          </p>
          <button
            onClick={forceFailure}
            className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2
              text-sm font-bold text-white hover:bg-red-700"
          >
            <AlertOctagon className="h-4 w-4" aria-hidden /> Force guard rejection
          </button>
          <p className="mt-2 text-xs text-slate-500">
            Sends a query with force_failure and switches to the Platform tab so you can
            watch the guard chip flip to REJECT.
          </p>
        </Panel>
      </div>

      <Panel title="Degradation paths" subtitle="FR-42/FR-43 · what happens when it breaks">
        <div className="space-y-2">
          {modes.map((m) => (
            <div key={m.id} className="rounded-lg border border-slate-200 p-3">
              <div className="flex flex-wrap items-center gap-2">
                <SlidersHorizontal className="h-4 w-4 text-slate-400" aria-hidden />
                <span className="text-sm font-bold text-slate-800">{m.label}</span>
                <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px]
                  font-bold text-slate-600">{m.rule}</span>
              </div>
              <p className="mt-1 text-xs text-slate-600">{m.effect}</p>
            </div>
          ))}
          {modes.length === 0 && (
            <p className="text-sm text-slate-500">Degradation modes unavailable.</p>
          )}
        </div>
      </Panel>
    </div>
  );
}
