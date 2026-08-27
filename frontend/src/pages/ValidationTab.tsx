import React, { useEffect, useState } from 'react';
import { CheckCircle2, Info, XCircle } from 'lucide-react';
import { api, Validation } from '../api/client';
import {
  ErrorState, Metric, Panel, ProvenanceBadge, Spinner,
} from '../components/ui/Primitives';

const pct = (v: number) => `${(v * 100).toFixed(1)}%`;

export default function ValidationTab() {
  const [data, setData] = useState<Validation | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    api.validation().then(setData).catch((e) => setError(e.message));
  };
  useEffect(load, []);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return <Spinner label="Computing contingency table…" />;

  const c = data.contingency;
  const b = data.baseline;
  const eq = data.skill.equal_pod_point;

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg
        border border-violet-200 bg-violet-50 p-3 text-sm text-violet-900">
        <span className="flex items-start gap-2">
          <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          <span>
            <strong>Ground truth is synthetic.</strong> These numbers are genuinely
            recomputed from the record on every request, so the method is real — but they
            are not a field skill claim. Replace the record and the incident list with
            observed data before quoting any of this.
          </span>
        </span>
        <ProvenanceBadge value={data.provenance} />
      </div>

      <p className="text-sm text-slate-600">
        Record: <strong>{data.record.days}</strong> days, {data.record.start} to{' '}
        {data.record.end}. Reference hull{' '}
        <strong>{data.reference_hull.replace(/_/g, ' ')}</strong>, operating point{' '}
        <strong className="font-mono">{data.threshold}</strong>.
      </p>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)]">
        <Panel title="Contingency table" subtitle={`${c.event_count} incident days`}>
          <div className="grid grid-cols-2 gap-2 text-center text-xs">
            <Cell n={c.hits} label="Hits" tone="emerald" />
            <Cell n={c.false_alarms} label="False alarms" tone="amber" />
            <Cell n={c.misses} label="Misses" tone="red" />
            <Cell n={c.correct_negatives} label="Correct negatives" tone="slate" />
          </div>
        </Panel>

        <div className="grid gap-3 sm:grid-cols-3">
          <Metric label="POD" value={pct(c.pod)} tone="good"
            sub={`${c.hits} of ${c.event_count} incidents flagged`} />
          <Metric label="FAR" value={pct(c.far)} tone="warn"
            sub="High: incidents are rare events" />
          <Metric label="Days flagged / yr" value={c.days_per_year.toFixed(0)}
            sub={`of 365 · baseline ${b.days_per_year.toFixed(0)}`} />
        </div>
      </div>

      <Panel
        title="Skill against the naive baseline"
        subtitle={data.skill.criterion}
        right={data.skill.beats_baseline ? (
          <span className="inline-flex items-center gap-1.5 rounded-full border
            border-emerald-300 bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-800">
            <CheckCircle2 className="h-4 w-4" aria-hidden /> Beats baseline
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 rounded-full border
            border-red-300 bg-red-50 px-3 py-1 text-xs font-bold text-red-800">
            <XCircle className="h-4 w-4" aria-hidden /> Does not beat baseline
          </span>
        )}
      >
        <p className="mb-4 text-sm text-slate-700">{data.skill.statement}</p>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[34rem] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="p-2.5">Model</th>
                <th className="p-2.5">Operating point</th>
                <th className="p-2.5">POD</th>
                <th className="p-2.5">FAR</th>
                <th className="p-2.5">Days / yr</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              <tr>
                <td className="p-2.5 font-medium">Naive baseline</td>
                <td className="p-2.5 font-mono text-xs">{b.definition}</td>
                <td className="p-2.5 tabular-nums">{pct(b.pod)}</td>
                <td className="p-2.5 tabular-nums">{pct(b.far)}</td>
                <td className="p-2.5 tabular-nums">{b.days_per_year.toFixed(0)}</td>
              </tr>
              {eq && (
                <tr className="bg-sky-50">
                  <td className="p-2.5 font-bold text-sky-900">
                    ORCA <span className="font-normal">(at equal POD)</span>
                  </td>
                  <td className="p-2.5 font-mono text-xs">index ≥ {eq.threshold}</td>
                  <td className="p-2.5 font-bold tabular-nums">{pct(eq.pod)}</td>
                  <td className={`p-2.5 font-bold tabular-nums ${eq.far < b.far
                    ? 'text-emerald-700' : 'text-red-700'}`}>{pct(eq.far)}</td>
                  <td className={`p-2.5 font-bold tabular-nums ${
                    eq.days_per_year < b.days_per_year ? 'text-emerald-700' : ''}`}>
                    {eq.days_per_year.toFixed(0)}
                  </td>
                </tr>
              )}
              <tr>
                <td className="p-2.5 font-medium">ORCA (current setting)</td>
                <td className="p-2.5 font-mono text-xs">index ≥ {data.threshold}</td>
                <td className="p-2.5 tabular-nums">{pct(c.pod)}</td>
                <td className="p-2.5 tabular-nums">{pct(c.far)}</td>
                <td className="p-2.5 tabular-nums">{c.days_per_year.toFixed(0)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Failure case" subtitle="A dated day the index got wrong">
          {data.failure_case ? (
            <div className="space-y-2 text-sm">
              <Row k="Date" v={data.failure_case.date} />
              <Row k="Index" v={`${data.failure_case.index_value} (threshold ${
                data.failure_case.threshold})`} />
              <Row k="Predicted" v={data.failure_case.predicted_verdict} />
              <Row k="Actual" v={data.failure_case.actual_outcome} />
              <Row k="Conditions" v={`Hs ${data.failure_case.conditions.hs_m} m · Tp ${
                data.failure_case.conditions.tp_s} s · tide ${
                data.failure_case.conditions.tide_stage}`} />
              <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3
                text-xs leading-relaxed text-red-900">
                <strong>Diagnosis:</strong> {data.failure_case.diagnosis}
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500">
              No missed incident at this operating point.
            </p>
          )}
        </Panel>

        <Panel title="Incident record"
          subtitle={`${data.incidents.length} dated days · ground truth`}>
          <div className="max-h-72 overflow-y-auto">
            <table className="w-full text-left text-xs">
              <thead className="sticky top-0 bg-white text-slate-500">
                <tr>
                  <th className="py-1.5">Date</th>
                  <th className="py-1.5">Index</th>
                  <th className="py-1.5">Hs</th>
                  <th className="py-1.5">Flagged?</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.incidents.map((i) => (
                  <tr key={i.date}>
                    <td className="py-1.5 font-mono">{i.date}</td>
                    <td className="py-1.5 tabular-nums">{i.index_value}</td>
                    <td className="py-1.5 tabular-nums">{i.hs_m} m</td>
                    <td className="py-1.5">
                      {i.flagged
                        ? <span className="font-bold text-emerald-700">hit</span>
                        : <span className="font-bold text-red-700">MISS</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-[11px] text-slate-500">
            No source URLs: these are generated records, not dated news reports.
          </p>
        </Panel>
      </div>

      <Panel title="Limits of this validation">
        <ul className="space-y-2 text-sm text-slate-700">
          {data.limits.map((l) => (
            <li key={l} className="flex gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400" />
              {l}
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}

function Cell({ n, label, tone }: { n: number; label: string; tone: string }) {
  const cls: Record<string, string> = {
    emerald: 'bg-emerald-50 text-emerald-900 border-emerald-200',
    amber: 'bg-amber-50 text-amber-900 border-amber-200',
    red: 'bg-red-50 text-red-900 border-red-200',
    slate: 'bg-slate-50 text-slate-800 border-slate-200',
  };
  return (
    <div className={`rounded-lg border p-4 ${cls[tone]}`}>
      <div className="text-2xl font-black tabular-nums">{n}</div>
      <div className="mt-0.5 font-medium">{label}</div>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex gap-3">
      <span className="w-24 shrink-0 text-xs font-bold uppercase text-slate-500">{k}</span>
      <span className="text-slate-800">{v}</span>
    </div>
  );
}
