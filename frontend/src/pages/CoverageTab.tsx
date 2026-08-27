import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { ErrorState, Spinner, StatusTag } from '../components/ui/Primitives';

interface Row {
  id: number; requirement: string; note: string; status: 'BUILT' | 'MOCKUP';
}

export default function CoverageTab() {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [summary, setSummary] = useState({ built: 0, mockup: 0, total: 0 });
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    api.coverage()
      .then((d) => { setRows(d.rows); setSummary(d.summary); })
      .catch((e) => setError(e.message));
  };
  useEffect(load, []);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!rows) return <Spinner label="Loading coverage matrix…" />;

  return (
    <div className="mx-auto max-w-5xl overflow-hidden rounded-xl border border-slate-200
      bg-white shadow-sm">
      <header className="flex flex-wrap items-center justify-between gap-3 bg-slate-900
        p-5 text-white">
        <div>
          <h2 className="text-xl font-bold">Requirement coverage</h2>
          <p className="mt-0.5 text-sm text-slate-400">
            Every PS requirement line, tagged honestly. A row is BUILT only if the running
            system does the thing.
          </p>
        </div>
        <div className="flex gap-3 rounded-lg border border-slate-700 bg-slate-800
          px-4 py-2 text-sm font-bold">
          <span className="text-emerald-400">{summary.built} built</span>
          <span className="text-slate-600">·</span>
          <span className="text-slate-300">{summary.mockup} mockup</span>
          <span className="text-slate-600">·</span>
          <span className="text-slate-400">{summary.total} total</span>
        </div>
      </header>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[46rem] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase
            text-slate-500">
            <tr>
              <th className="px-4 py-3">#</th>
              <th className="px-4 py-3">Requirement</th>
              <th className="px-4 py-3">What exists</th>
              <th className="px-4 py-3 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {rows.map((r) => (
              <tr key={r.id} className={r.status === 'MOCKUP' ? 'bg-slate-50/60' : ''}>
                <td className="px-4 py-3 font-mono text-xs text-slate-400">
                  {String(r.id).padStart(2, '0')}
                </td>
                <td className="px-4 py-3 font-medium text-slate-800">{r.requirement}</td>
                <td className="px-4 py-3 text-xs leading-relaxed text-slate-600">
                  {r.note}
                </td>
                <td className="px-4 py-3 text-right"><StatusTag status={r.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <footer className="border-t border-slate-200 bg-slate-50 px-4 py-3 text-xs
        text-slate-500">
        This table is read from config (D-12), not hardcoded in the page. Editing that
        file changes what is claimed here.
      </footer>
    </div>
  );
}
