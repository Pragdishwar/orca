import React, { useEffect, useState } from 'react';
import { Bell, ChevronDown, ChevronRight, Radio, RefreshCw } from 'lucide-react';
import { api, AlertRow, BroadcastBundle } from '../api/client';
import { useOrcaStore } from '../store/useOrcaStore';
import {
  EmptyState, ErrorState, Panel, Spinner, VerdictBadge,
} from '../components/ui/Primitives';

type Filter = 'all' | 'severe' | 'warning' | 'advisory';

const SEVERITY_STYLE: Record<string, string> = {
  severe: 'border-red-300 bg-red-50 text-red-900',
  warning: 'border-amber-300 bg-amber-50 text-amber-900',
  advisory: 'border-sky-300 bg-sky-50 text-sky-900',
};

export default function AlertsTab() {
  const { alerts, alertSummary, refreshAlerts } = useOrcaStore();
  const [filter, setFilter] = useState<Filter>('all');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState(false);
  const [officer, setOfficer] = useState('');
  const [roster, setRoster] = useState<
    { officer_id: string; name: string; role: string }[]>([]);
  const [rosterNote, setRosterNote] = useState('');
  const [open, setOpen] = useState<string | null>(null);
  const [broadcast, setBroadcast] = useState<Record<string, BroadcastBundle>>({});

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      await refreshAlerts();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Alerts unavailable');
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { load(); }, []);
  useEffect(() => {
    api.officers()
      .then((d) => { setRoster(d.officers); setRosterNote(d.note); })
      .catch(() => setRoster([]));
  }, []);

  const runPoll = async () => {
    setPolling(true);
    try {
      await api.sentinelTrigger();
      await refreshAlerts();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Poll failed');
    } finally {
      setPolling(false);
    }
  };

  const release = async (id: string) => {
    if (!officer.trim()) return;
    try {
      await api.releaseAlert(id, officer.trim());
      await refreshAlerts();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Release failed');
    }
  };

  const expand = async (id: string) => {
    setOpen(open === id ? null : id);
    if (!broadcast[id]) {
      try {
        const bundle = await api.alertBroadcast(id);
        setBroadcast((b) => ({ ...b, [id]: bundle }));
      } catch { /* the row shows without its compile preview */ }
    }
  };

  const rows = filter === 'all' ? alerts : alerts.filter((a) => a.severity === filter);

  return (
    <div className="mx-auto max-w-5xl space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Sentinel alerts</h2>
          <p className="text-sm text-slate-500">
            Generated on a schedule, with no question asked.
          </p>
        </div>
        <button
          onClick={runPoll}
          disabled={polling}
          className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-2
            text-sm font-semibold text-white hover:bg-slate-700 disabled:bg-slate-400"
        >
          <RefreshCw className={`h-4 w-4 ${polling ? 'animate-spin' : ''}`} aria-hidden />
          {polling ? 'Polling…' : 'Run a poll cycle now'}
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {(['all', 'severe', 'warning', 'advisory'] as Filter[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-full border px-3 py-1 text-xs font-semibold capitalize
              ${filter === f
                ? 'border-slate-900 bg-slate-900 text-white'
                : 'border-slate-300 bg-white text-slate-600 hover:bg-slate-100'}`}
          >
            {f}
            {f !== 'all' && ` (${alertSummary[f] ?? 0})`}
          </button>
        ))}
        <span className="ml-auto text-xs text-slate-500">
          {alertSummary.pending_release ?? 0} awaiting release ·{' '}
          {alertSummary.released ?? 0} released
        </span>
      </div>

      <div className={`rounded-lg border p-3 ${officer.trim()
        ? 'border-emerald-300 bg-emerald-50' : 'border-amber-300 bg-amber-50'}`}>
        <div className="flex flex-wrap items-end gap-3">
          <label className="min-w-[16rem] flex-1">
            <span className="text-xs font-bold uppercase text-slate-600">
              Step 1 — Authorising officer (R-4)
            </span>
            <select
              value={officer}
              onChange={(e) => setOfficer(e.target.value)}
              className="mt-1 w-full rounded border border-slate-300 bg-white px-3 py-2
                text-sm outline-none focus:ring-2 focus:ring-sky-500"
            >
              <option value="">Select an authorised officer…</option>
              {roster.map((o) => (
                <option key={o.officer_id} value={o.officer_id}>
                  {o.name} · {o.officer_id}
                </option>
              ))}
            </select>
          </label>
          <p className={`flex-1 text-xs ${officer.trim()
            ? 'text-emerald-800' : 'text-amber-900'}`}>
            {officer.trim() ? (
              <>
                <strong>Release enabled.</strong> Recorded as authorised by{' '}
                <strong>{roster.find((o) => o.officer_id === officer)?.name ?? officer}</strong>.
              </>
            ) : (
              <>
                <strong>Release is locked.</strong> Only posts on the authorisation
                roster may release an advisory — free text is rejected by the server.
                Pick an officer to unlock the Release buttons.
              </>
            )}
          </p>
        </div>
      </div>

      {error && <ErrorState message={error} onRetry={load} />}
      {loading && <Spinner label="Loading alerts…" />}
      {!loading && !error && rows.length === 0 && (
        <EmptyState
          title="No active alerts"
          hint="Run a poll cycle, or wait for the scheduled interval."
        />
      )}

      <div className="space-y-3">
        {rows.map((a) => (
          <article key={a.alert_id}
            className="overflow-hidden rounded-xl border border-slate-200 bg-white
              shadow-sm">
            <div className="flex flex-wrap items-start gap-3 p-4">
              <span className={`rounded-full border px-2.5 py-1 text-[10px] font-bold
                uppercase ${SEVERITY_STYLE[a.severity]}`}>
                {a.severity}
              </span>
              <div className="min-w-[12rem] flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <VerdictBadge verdict={a.verdict ?? 'UNKNOWN'} size="sm" />
                  <span className="text-sm font-bold text-slate-800">{a.boat_id}</span>
                  <span className="text-xs text-slate-500">
                    {a.hull_class?.replace(/_/g, ' ')}
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  {a.trigger_type} · for {a.trigger_detail?.for_date ?? '—'} · index{' '}
                  <span className="font-mono">{a.index_value}</span>
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`rounded px-2 py-1 text-[10px] font-bold ${
                  a.state === 'RELEASED'
                    ? 'bg-emerald-100 text-emerald-800'
                    : 'bg-slate-100 text-slate-700'}`}>
                  {a.state.replace('_', ' ')}
                </span>
                {a.state === 'PENDING_RELEASE' ? (
                  <button
                    onClick={() => release(a.alert_id)}
                    disabled={!officer.trim()}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-sky-600
                      px-3 py-1.5 text-xs font-bold text-white hover:bg-sky-700
                      disabled:bg-slate-300 disabled:text-slate-500"
                    title={officer.trim()
                      ? `Release as ${officer.trim()}`
                      : 'Enter an officer name above to enable this'}
                  >
                    <Radio className="h-3.5 w-3.5" aria-hidden />
                    {officer.trim() ? 'Release' : 'Release — name needed'}
                  </button>
                ) : (
                  <span className="text-[11px] text-slate-500">by {a.released_by}</span>
                )}
                <button onClick={() => expand(a.alert_id)}
                  aria-label="Trigger detail"
                  className="rounded p-1.5 text-slate-500 hover:bg-slate-100">
                  {open === a.alert_id
                    ? <ChevronDown className="h-4 w-4" aria-hidden />
                    : <ChevronRight className="h-4 w-4" aria-hidden />}
                </button>
              </div>
            </div>

            {open === a.alert_id && (
              <div className="space-y-3 border-t border-slate-200 bg-slate-50 p-4">
                <div>
                  <h4 className="text-xs font-bold uppercase text-slate-500">
                    Trigger detail
                  </h4>
                  <p className="mt-1 text-sm text-slate-700">
                    {a.trigger_detail?.explanation}
                  </p>
                  <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs
                    sm:grid-cols-4">
                    {['hs_m', 'wind_ms', 'index_value', 'source_id'].map((k) => (
                      <div key={k}>
                        <dt className="text-slate-500">{k}</dt>
                        <dd className="font-mono text-slate-800">
                          {String(a.trigger_detail?.[k] ?? '—')}
                        </dd>
                      </div>
                    ))}
                  </dl>
                </div>

                {broadcast[a.alert_id] && (
                  <div>
                    <h4 className="text-xs font-bold uppercase text-slate-500">
                      Compiles to the same four formats
                    </h4>
                    <pre className="mt-1 overflow-x-auto rounded border border-slate-200
                      bg-white p-2 font-mono text-[11px] text-slate-700">
{broadcast[a.alert_id].sms.content}
                    </pre>
                    <p className="mt-1 text-[10px] text-slate-500">
                      SMS {broadcast[a.alert_id].sms.char_count}/
                      {broadcast[a.alert_id].sms.limit} chars ·{' '}
                      {broadcast[a.alert_id].notice}
                    </p>
                  </div>
                )}
              </div>
            )}
          </article>
        ))}
      </div>

      <Panel>
        <p className="flex items-start gap-2 text-sm text-slate-600">
          <Bell className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" aria-hidden />
          An alert is a different trigger for the same pipeline a question uses — the same
          hazard index, the same hull thresholds, the same release gate, the same four
          broadcast formats. There is no separate alerting path.
          {rosterNote && <><br /><br /><strong>On access control:</strong> {rosterNote}</>}
        </p>
      </Panel>
    </div>
  );
}
